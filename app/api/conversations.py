"""
API endpoints for managing conversations.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.core.di import get_conversation_manager
from app.domain.models import Conversation, ConversationListResponse

router = APIRouter()


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    conversation_manager = Depends(get_conversation_manager)
):
    """List all active conversations with summary metadata."""
    conversations = conversation_manager.list_conversations()
    
    return ConversationListResponse(
        conversations=conversations,
        total=len(conversations)
    )


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    conversation_manager = Depends(get_conversation_manager)
):
    """Get full details of a specific conversation."""
    conversation = conversation_manager.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    conversation_manager = Depends(get_conversation_manager)
):
    """Delete a conversation."""
    success = conversation_manager.delete_conversation(conversation_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": "Conversation deleted successfully", "conversation_id": conversation_id}


@router.delete("/conversations")
async def clear_all_conversations(
    conversation_manager = Depends(get_conversation_manager)
):
    """Clear all conversations (useful for testing/cleanup)."""
    conversation_manager.clear_all()
    
    return {"message": "All conversations cleared"}
