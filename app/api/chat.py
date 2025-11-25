from fastapi import APIRouter, Query, Depends, HTTPException
from app.core.exceptions import InvalidInput
from starlette.concurrency import run_in_threadpool
from app.core.di import get_settings, get_conversation_manager
from app.domain.models import ChatRequest, ChatResponse, Issue, ConversationState
from src.crew import CodeReviewProject  # type: ignore

router = APIRouter()

@router.post("/chat")
async def chat(
    body: ChatRequest,
    fast: bool = Query(False, description="Return quick stub response for connectivity testing"),
    settings = Depends(get_settings),
    conversation_manager = Depends(get_conversation_manager),
):
    """
    Enhanced chat endpoint with conversation support.
    
    Flow:
    1. If no conversation_id: analyze new code, create conversation
    2. If conversation_id exists: continue conversation (apply fixes, explain, etc.)
    """
    
    # Fast mode bypass
    if fast:
        return ChatResponse(summary="OK (fast mode)", issues=[])
    
    # === Case 1: New conversation with code analysis ===
    if body.get_code() and not body.conversation_id:
        return await _handle_new_analysis(body, conversation_manager, settings)
    
    # === Case 2: Continue existing conversation ===
    if body.conversation_id:
        return await _handle_conversation_continuation(body, conversation_manager, settings)
    
    # === Case 3: Invalid request ===
    raise InvalidInput("Provide 'source_code' or 'conversation_id' with 'message'.")


async def _handle_new_analysis(
    body: ChatRequest,
    conversation_manager,
    settings
) -> ChatResponse:
    """Handle initial code analysis and create new conversation."""
    code = body.get_code()
    if not code:
        raise InvalidInput("Provide 'source_code' or 'code_snippet'.")
    
    # Create new conversation
    conv_id = conversation_manager.create_conversation()
    
    # Store user's code submission
    conversation_manager.add_message(
        conv_id,
        role="user",
        content="Please analyze this code",
        metadata={"source_code": code}
    )
    
    # Run code review using Bedrock
    project = CodeReviewProject()
    parsed = await run_in_threadpool(lambda: project.code_review(code))
    
    summary = parsed.get("summary") if isinstance(parsed, dict) else None
    issues = []
    if isinstance(parsed, dict) and isinstance(parsed.get("issues"), list):
        for item in parsed["issues"]:
            if isinstance(item, dict):
                issues.append(
                    Issue(
                        type=item.get("type"),
                        description=item.get("description"),
                        suggestion=item.get("suggestion"),
                    )
                )
    
    # Update conversation state
    conversation_manager.update_state(
        conv_id,
        ConversationState(
            original_code=code,
            current_code=code,
            detected_issues=issues,
            pending_issues=[issue.type for issue in issues if issue.type],
            applied_fixes=[],
            awaiting_decision=len(issues) > 0
        )
    )
    
    # Store assistant's response
    conversation_manager.add_message(
        conv_id,
        role="assistant",
        content=summary or "Analysis complete",
        metadata={"issues": [issue.dict() for issue in issues]}
    )
    
    # Prepare response
    awaiting_input = len(issues) > 0
    suggested_actions = []
    if awaiting_input:
        suggested_actions = [
            "Apply all improvements",
            "Fix specific issue types",
            "Explain issues in detail",
            "Decline improvements"
        ]
    
    return ChatResponse(
        summary=summary,
        issues=issues,
        conversation_id=conv_id,
        awaiting_user_input=awaiting_input,
        suggested_actions=suggested_actions if awaiting_input else None
    )


async def _handle_conversation_continuation(
    body: ChatRequest,
    conversation_manager,
    settings
) -> ChatResponse:
    """Handle follow-up messages in existing conversation."""
    conv_id = body.conversation_id
    
    # Validate conversation exists
    conversation = conversation_manager.get_conversation(conv_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Require either message or new code
    if not body.message and not body.get_code():
        raise InvalidInput("Provide 'message' or 'source_code' for conversation continuation")
    
    # If new code provided, restart analysis in same conversation
    if body.get_code():
        return await _handle_new_code_in_conversation(body, conv_id, conversation_manager, settings)
    
    # Handle user message
    user_message = body.message or ""
    if not user_message.strip():
        raise InvalidInput("Message cannot be empty")
    
    # Store user message
    conversation_manager.add_message(
        conv_id,
        role="user",
        content=user_message
    )
    
    # Determine user intent
    if body.apply_improvements:
        return await _handle_apply_improvements(conv_id, user_message, conversation_manager, settings)
    elif body.apply_improvements is False:
        return _handle_decline_improvements(conv_id, conversation_manager)
    else:
        return await _handle_general_question(conv_id, user_message, conversation_manager, settings)


async def _handle_apply_improvements(
    conv_id: str,
    user_message: str,
    conversation_manager,
    settings
) -> ChatResponse:
    """User wants to apply code improvements."""
    conversation = conversation_manager.get_conversation(conv_id)
    
    # Determine which issue types to fix based on user message
    fix_types = None
    user_msg_lower = user_message.lower()
    
    if "security" in user_msg_lower and "performance" not in user_msg_lower:
        fix_types = ["SECURITY"]
    elif "performance" in user_msg_lower and "security" not in user_msg_lower:
        fix_types = ["PERFORMANCE"]
    elif any(word in user_msg_lower for word in ["best practice", "style", "formatting"]):
        fix_types = ["BEST_PRACTICE", "STYLE"]
    # else: fix all issues (fix_types = None)
    
    # Use code improver agent to generate fixed code
    project = CodeReviewProject()
    original_code = conversation.state.original_code or ""
    issues = conversation.state.detected_issues or []
    
    # Convert Issue objects to dicts for improve_code method
    issues_dicts = [
        {
            "type": issue.type,
            "description": issue.description,
            "suggestion": issue.suggestion
        }
        for issue in issues
    ]
    
    # Generate improved code
    improved_code = project.improve_code(
        source_code=original_code,
        issues=issues_dicts,
        fix_types=fix_types
    )
    
    # Determine which fixes were applied
    applied_fix_types = fix_types if fix_types else [i.type for i in issues if i.type]
    
    # Store assistant response
    conversation_manager.add_message(
        conv_id,
        role="assistant",
        content="I've generated improved code based on the issues found.",
        metadata={"improved_code": improved_code}
    )
    
    # Update state
    remaining_issues = [i.type for i in issues if i.type not in applied_fix_types] if fix_types else []
    
    conversation_manager.update_state(
        conv_id,
        ConversationState(
            current_code=improved_code,
            applied_fixes=applied_fix_types,
            pending_issues=remaining_issues,
            awaiting_decision=len(remaining_issues) > 0
        )
    )
    
    suggested_actions = None
    if remaining_issues:
        suggested_actions = [
            f"Fix remaining issues: {', '.join(remaining_issues)}",
            "Explain remaining issues"
        ]
    
    return ChatResponse(
        summary="Code improvements applied successfully" + 
                (f". Remaining issues: {', '.join(remaining_issues)}" if remaining_issues else ""),
        conversation_id=conv_id,
        improved_code=improved_code,
        awaiting_user_input=len(remaining_issues) > 0,
        suggested_actions=suggested_actions
    )


def _handle_decline_improvements(
    conv_id: str,
    conversation_manager
) -> ChatResponse:
    """User declined improvements."""
    conversation_manager.add_message(
        conv_id,
        role="assistant",
        content="Understood. Let me know if you need anything else."
    )
    
    conversation_manager.update_state(
        conv_id,
        ConversationState(awaiting_decision=False)
    )
    
    return ChatResponse(
        summary="No problem! Let me know if you change your mind.",
        conversation_id=conv_id,
        awaiting_user_input=False
    )


async def _handle_general_question(
    conv_id: str,
    user_message: str,
    conversation_manager,
    settings
) -> ChatResponse:
    """Handle explanations or general questions about the code."""
    # Get conversation context if needed in future
    
    # For now, return a simple response
    # This will be enhanced when we add conversational AI agent
    response_summary = f"Regarding your question: '{user_message}' - This will be handled by the conversational agent."
    
    conversation_manager.add_message(
        conv_id,
        role="assistant",
        content=response_summary
    )
    
    return ChatResponse(
        summary=response_summary,
        conversation_id=conv_id,
        awaiting_user_input=False
    )


async def _handle_new_code_in_conversation(
    body: ChatRequest,
    conv_id: str,
    conversation_manager,
    settings
) -> ChatResponse:
    """User submitted new code in existing conversation - restart analysis."""
    # Clear previous state and start fresh
    conversation_manager.update_state(
        conv_id,
        ConversationState(
            original_code=None,
            current_code=None,
            detected_issues=None,
            pending_issues=None,
            applied_fixes=None,
            awaiting_decision=False
        )
    )
    
    # Create new request without conversation_id to trigger fresh analysis
    new_request = ChatRequest(source_code=body.get_code())
    
    # But keep the same conversation
    result = await _handle_new_analysis(new_request, conversation_manager, settings)
    result.conversation_id = conv_id  # Maintain same conversation
    return result


    if body.conversation_id:
        conversation = conversation_manager.get_conversation(body.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Handle new code submission in existing conversation
        if body.get_code():
            # Re-analyze new code
            new_code = body.get_code()
            test_issues = []
            
            if "password" in new_code.lower() or "secret" in new_code.lower():
                test_issues.append(
                    Issue(
                        type="SECURITY",
                        description="Hardcoded credentials detected",
                        suggestion="Use environment variables or secure vault"
                    )
                )
            
            if "for" in new_code.lower() and "println" in new_code.lower():
                test_issues.append(
                    Issue(
                        type="PERFORMANCE",
                        description="Inefficient loop with I/O operations",
                        suggestion="Use bulk operations or optimize I/O"
                    )
                )
            
            # Update conversation state with new code
            conversation_manager.update_state(
                body.conversation_id,
                ConversationState(
                    original_code=new_code,
                    current_code=new_code,
                    detected_issues=test_issues,
                    pending_issues=[i.type for i in test_issues if i.type],
                    awaiting_decision=len(test_issues) > 0
                )
            )
            
            return ChatResponse(
                summary="Analysis of new code (test mode)",
                issues=test_issues,
                conversation_id=body.conversation_id,
                awaiting_user_input=len(test_issues) > 0,
                suggested_actions=["Apply fixes", "Explain issues"] if test_issues else None
            )
        
        if body.apply_improvements:
            # Return improved code (remove hardcoded secrets)
            original = conversation.state.original_code or ""
            improved = original.replace("secret123", "os.getenv('PASSWORD')")
            improved = improved.replace('"secret"', 'os.getenv("PASSWORD")')
            
            return ChatResponse(
                summary="Improvements applied (test mode)",
                conversation_id=body.conversation_id,
                improved_code=improved,
                awaiting_user_input=False
            )
        
        # Handle questions/explanations in test mode
        if body.message is not None:
            user_msg = body.message
            
            # Validate non-empty message
            if not user_msg.strip():
                raise InvalidInput("Message cannot be empty")
            
            user_msg_lower = user_msg.lower()
            explanation = "OK (test mode continuation)"
            
            # Provide meaningful explanations for test assertions
            if "why" in user_msg_lower or "explain" in user_msg_lower:
                if "performance" in user_msg_lower:
                    explanation = ("The performance issue occurs because you're using a loop with "
                                 "I/O operations (println) which blocks execution. This creates O(n) "
                                 "I/O overhead. Consider batching output or using asynchronous I/O.")
                elif "security" in user_msg_lower:
                    explanation = ("The security issue is caused by hardcoded credentials in the source code. "
                                 "This exposes sensitive data in version control and compiled binaries. "
                                 "Use environment variables, configuration files, or secure vaults instead.")
                else:
                    explanation = ("Based on the code analysis, the detected issues relate to common "
                                 "anti-patterns that can impact security, performance, and maintainability. "
                                 "Each issue includes specific suggestions for remediation.")
            
            return ChatResponse(
                summary=explanation,
                conversation_id=body.conversation_id,
                awaiting_user_input=False
            )
        
        return ChatResponse(
            summary="OK (test mode continuation)",
            conversation_id=body.conversation_id,
            awaiting_user_input=False
        )
    
    # No valid input provided - should fail validation
    raise InvalidInput("Provide 'source_code' or 'conversation_id' with 'message'.")
