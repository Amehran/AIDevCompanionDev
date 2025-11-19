"""
ConversationManager service - Handles multi-turn conversation state and history.

TDD Implementation: Building to pass the tests in test_conversation_manager.py
"""

from typing import Optional, Dict, Any, List
from threading import Lock
from datetime import datetime
from app.domain.models import Conversation, ConversationState, Message


class ConversationManager:
    """
    Manages conversation sessions with message history and state tracking.
    
    Thread-safe in-memory storage for MVP. Can be extended to use Redis or
    database for production persistence.
    """
    
    def __init__(self):
        """Initialize the conversation manager with empty storage."""
        self._conversations: Dict[str, Conversation] = {}
        self._lock = Lock()
    
    def create_conversation(self) -> str:
        """
        Create a new conversation and return its ID.
        
        Returns:
            Unique conversation ID
        """
        with self._lock:
            conversation = Conversation()
            self._conversations[conversation.conversation_id] = conversation
            return conversation.conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve a conversation by ID.
        
        Args:
            conversation_id: The conversation identifier
            
        Returns:
            Conversation object or None if not found
        """
        with self._lock:
            return self._conversations.get(conversation_id)
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to the conversation.
        
        Args:
            conversation_id: Target conversation ID
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata dict
        """
        with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation is None:
                return
            
            message = Message(
                role=role,  # type: ignore
                content=content,
                metadata=metadata
            )
            conversation.messages.append(message)
            conversation.updated_at = datetime.now().timestamp()
    
    def update_state(
        self,
        conversation_id: str,
        state: ConversationState
    ) -> None:
        """
        Update the conversation state.
        
        Args:
            conversation_id: Target conversation ID
            state: New state object
        """
        with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation is None:
                return
            
            # Merge state - update only non-None fields
            if state.original_code is not None:
                conversation.state.original_code = state.original_code
            if state.current_code is not None:
                conversation.state.current_code = state.current_code
            if state.detected_issues is not None:
                conversation.state.detected_issues = state.detected_issues
            if state.pending_issues is not None:
                conversation.state.pending_issues = state.pending_issues
            if state.applied_fixes is not None:
                conversation.state.applied_fixes = state.applied_fixes
            if state.awaiting_decision is not None:
                conversation.state.awaiting_decision = state.awaiting_decision
            
            conversation.updated_at = datetime.now().timestamp()
    
    def get_conversation_context(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get formatted conversation context for passing to AI agents.
        
        Args:
            conversation_id: Target conversation ID
            
        Returns:
            Dict with messages, state, and metadata for agent consumption
        """
        with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation is None:
                return None
            
            return {
                "conversation_id": conversation.conversation_id,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                        "metadata": msg.metadata
                    }
                    for msg in conversation.messages
                ],
                "state": {
                    "original_code": conversation.state.original_code,
                    "current_code": conversation.state.current_code,
                    "detected_issues": conversation.state.detected_issues,
                    "pending_issues": conversation.state.pending_issues,
                    "applied_fixes": conversation.state.applied_fixes,
                    "awaiting_decision": conversation.state.awaiting_decision
                }
            }
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Target conversation ID
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if conversation_id in self._conversations:
                del self._conversations[conversation_id]
                return True
            return False
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all conversations with summary metadata.
        
        Returns:
            List of conversation summaries
        """
        with self._lock:
            return [
                {
                    "conversation_id": conv.conversation_id,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "message_count": len(conv.messages)
                }
                for conv in self._conversations.values()
            ]
    
    def clear_all(self) -> None:
        """Clear all conversations (for testing)."""
        with self._lock:
            self._conversations.clear()
