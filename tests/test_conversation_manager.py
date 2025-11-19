"""
Tests for ConversationManager service.

Following TDD: These tests define the expected behavior before implementation.
"""

from app.services.conversation_manager import ConversationManager
from app.domain.models import ConversationState, Issue


class TestConversationManager:
    """Test suite for ConversationManager."""
    
    def setup_method(self):
        """Create a fresh ConversationManager for each test."""
        self.manager = ConversationManager()
    
    # ========================================================================
    # Basic Conversation Creation & Retrieval
    # ========================================================================
    
    def test_create_new_conversation(self):
        """Should create a new conversation and return conversation_id."""
        conv_id = self.manager.create_conversation()
        
        assert conv_id is not None
        assert isinstance(conv_id, str)
        assert len(conv_id) > 0
    
    def test_get_existing_conversation(self):
        """Should retrieve an existing conversation by ID."""
        conv_id = self.manager.create_conversation()
        
        conversation = self.manager.get_conversation(conv_id)
        
        assert conversation is not None
        assert conversation.conversation_id == conv_id
        assert isinstance(conversation.messages, list)
        assert len(conversation.messages) == 0  # New conversation has no messages
    
    def test_get_nonexistent_conversation_returns_none(self):
        """Should return None when conversation doesn't exist."""
        conversation = self.manager.get_conversation("nonexistent-id")
        
        assert conversation is None
    
    # ========================================================================
    # Message Management
    # ========================================================================
    
    def test_add_user_message(self):
        """Should add a user message to conversation."""
        conv_id = self.manager.create_conversation()
        
        self.manager.add_message(
            conv_id,
            role="user",
            content="Analyze this code",
            metadata={"source_code": "fun main() {}"}
        )
        
        conversation = self.manager.get_conversation(conv_id)
        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == "user"
        assert conversation.messages[0].content == "Analyze this code"
        assert conversation.messages[0].metadata["source_code"] == "fun main() {}"
    
    def test_add_assistant_message(self):
        """Should add an assistant message to conversation."""
        conv_id = self.manager.create_conversation()
        
        self.manager.add_message(
            conv_id,
            role="assistant",
            content="Found 2 issues",
            metadata={"issues": ["PERFORMANCE", "SECURITY"]}
        )
        
        conversation = self.manager.get_conversation(conv_id)
        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == "assistant"
    
    def test_add_multiple_messages_preserves_order(self):
        """Should maintain message order in conversation history."""
        conv_id = self.manager.create_conversation()
        
        self.manager.add_message(conv_id, "user", "First message")
        self.manager.add_message(conv_id, "assistant", "Second message")
        self.manager.add_message(conv_id, "user", "Third message")
        
        conversation = self.manager.get_conversation(conv_id)
        assert len(conversation.messages) == 3
        assert conversation.messages[0].content == "First message"
        assert conversation.messages[1].content == "Second message"
        assert conversation.messages[2].content == "Third message"
    
    def test_add_message_updates_timestamp(self):
        """Should update conversation updated_at when adding messages."""
        conv_id = self.manager.create_conversation()
        conversation = self.manager.get_conversation(conv_id)
        initial_timestamp = conversation.updated_at
        
        import time
        time.sleep(0.01)  # Small delay to ensure timestamp difference
        
        self.manager.add_message(conv_id, "user", "New message")
        updated_conversation = self.manager.get_conversation(conv_id)
        
        assert updated_conversation.updated_at > initial_timestamp
    
    # ========================================================================
    # State Management
    # ========================================================================
    
    def test_update_conversation_state(self):
        """Should update the conversation state."""
        conv_id = self.manager.create_conversation()
        
        new_state = ConversationState(
            original_code="fun main() {}",
            current_code="fun main() {}",
            detected_issues=[
                Issue(type="PERFORMANCE", description="Slow loop", suggestion="Use sequence")
            ],
            pending_issues=["PERFORMANCE"],
            applied_fixes=[],
            awaiting_decision=True
        )
        
        self.manager.update_state(conv_id, new_state)
        
        conversation = self.manager.get_conversation(conv_id)
        assert conversation.state.original_code == "fun main() {}"
        assert conversation.state.awaiting_decision is True
        assert len(conversation.state.detected_issues) == 1
        assert conversation.state.pending_issues == ["PERFORMANCE"]
    
    def test_update_state_partial_fields(self):
        """Should allow updating only specific state fields."""
        conv_id = self.manager.create_conversation()
        
        # Set initial state
        initial_state = ConversationState(
            original_code="fun main() {}",
            pending_issues=["PERFORMANCE", "SECURITY"]
        )
        self.manager.update_state(conv_id, initial_state)
        
        # Update only some fields
        partial_state = ConversationState(
            applied_fixes=["SECURITY"],
            pending_issues=["PERFORMANCE"]
        )
        self.manager.update_state(conv_id, partial_state)
        
        conversation = self.manager.get_conversation(conv_id)
        assert conversation.state.applied_fixes == ["SECURITY"]
        assert conversation.state.pending_issues == ["PERFORMANCE"]
    
    # ========================================================================
    # Context Retrieval for Agents
    # ========================================================================
    
    def test_get_conversation_context(self):
        """Should retrieve formatted context for passing to AI agents."""
        conv_id = self.manager.create_conversation()
        
        self.manager.add_message(conv_id, "user", "Analyze this code", 
                                metadata={"source_code": "fun main() {}"})
        self.manager.add_message(conv_id, "assistant", "Found issues")
        self.manager.add_message(conv_id, "user", "Fix the security issue")
        
        context = self.manager.get_conversation_context(conv_id)
        
        assert context is not None
        assert "messages" in context
        assert len(context["messages"]) == 3
        assert "state" in context
        assert context["conversation_id"] == conv_id
    
    def test_get_context_includes_state(self):
        """Should include conversation state in context."""
        conv_id = self.manager.create_conversation()
        
        state = ConversationState(
            original_code="fun main() {}",
            pending_issues=["PERFORMANCE"]
        )
        self.manager.update_state(conv_id, state)
        
        context = self.manager.get_conversation_context(conv_id)
        
        assert context["state"]["original_code"] == "fun main() {}"
        assert context["state"]["pending_issues"] == ["PERFORMANCE"]
    
    # ========================================================================
    # Conversation Lifecycle
    # ========================================================================
    
    def test_delete_conversation(self):
        """Should delete a conversation."""
        conv_id = self.manager.create_conversation()
        self.manager.add_message(conv_id, "user", "Test message")
        
        result = self.manager.delete_conversation(conv_id)
        
        assert result is True
        assert self.manager.get_conversation(conv_id) is None
    
    def test_delete_nonexistent_conversation(self):
        """Should return False when deleting nonexistent conversation."""
        result = self.manager.delete_conversation("nonexistent-id")
        
        assert result is False
    
    def test_list_all_conversations(self):
        """Should list all active conversations."""
        conv_id_1 = self.manager.create_conversation()
        conv_id_2 = self.manager.create_conversation()
        
        conversations = self.manager.list_conversations()
        
        assert len(conversations) == 2
        conv_ids = [c["conversation_id"] for c in conversations]
        assert conv_id_1 in conv_ids
        assert conv_id_2 in conv_ids
    
    def test_list_conversations_includes_metadata(self):
        """Should include useful metadata in conversation list."""
        conv_id = self.manager.create_conversation()
        self.manager.add_message(conv_id, "user", "Message 1")
        self.manager.add_message(conv_id, "assistant", "Message 2")
        
        conversations = self.manager.list_conversations()
        
        assert len(conversations) == 1
        conv_summary = conversations[0]
        assert conv_summary["conversation_id"] == conv_id
        assert conv_summary["message_count"] == 2
        assert "created_at" in conv_summary
        assert "updated_at" in conv_summary
    
    def test_clear_all_conversations(self):
        """Should clear all conversations."""
        self.manager.create_conversation()
        self.manager.create_conversation()
        
        self.manager.clear_all()
        
        conversations = self.manager.list_conversations()
        assert len(conversations) == 0
    
    # ========================================================================
    # Thread Safety
    # ========================================================================
    
    def test_concurrent_message_addition(self):
        """Should handle concurrent message additions safely."""
        import threading
        
        conv_id = self.manager.create_conversation()
        
        def add_messages():
            for i in range(10):
                self.manager.add_message(conv_id, "user", f"Message {i}")
        
        threads = [threading.Thread(target=add_messages) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        conversation = self.manager.get_conversation(conv_id)
        # Should have 30 messages total (3 threads × 10 messages)
        assert len(conversation.messages) == 30
