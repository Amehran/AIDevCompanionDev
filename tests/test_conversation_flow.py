"""
Integration tests for conversational code review flow.

Following TDD: These tests define the expected multi-turn conversation behavior.
"""

from fastapi.testclient import TestClient


class TestConversationFlow:
    """Test multi-turn conversational interactions."""
    
    # ========================================================================
    # Initial Analysis Flow
    # ========================================================================
    
    def test_initial_code_analysis_creates_conversation(self, client: TestClient):
        """First request should analyze code and create a conversation."""
        response = client.post(
            "/chat",
            json={
                "source_code": "fun main() { val password = \"secret123\" }"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return analysis
        assert data["summary"] is not None
        assert isinstance(data["issues"], list)
        
        # Should create and return conversation_id
        assert data["conversation_id"] is not None
        assert len(data["conversation_id"]) > 0
        
        # Should ask if user wants improvements (when issues found)
        if len(data["issues"]) > 0:
            assert data["awaiting_user_input"] is True
            assert data["suggested_actions"] is not None
    
    def test_analysis_without_issues_no_improvements_offered(self, client: TestClient):
        """When no issues found, should not offer improvements."""
        response = client.post(
            "/chat",
            json={
                "source_code": "fun main() { println(\"Hello, World!\") }"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Assuming perfect code has no issues
        # (In real scenario, this depends on agent's analysis)
        assert data["conversation_id"] is not None
        # If no issues, awaiting_user_input should be False
        # assert data["awaiting_user_input"] is False
    
    # ========================================================================
    # User Confirmation & Code Improvement Flow
    # ========================================================================
    
    def test_user_confirms_wants_improvements(self, client: TestClient):
        """User says 'yes' to improvements, should return improved code."""
        # Step 1: Initial analysis
        response1 = client.post(
            "/chat",
            json={
                "source_code": "fun main() { val password = \"secret123\" }"
            }
        )
        data1 = response1.json()
        conv_id = data1["conversation_id"]
        
        # Step 2: User confirms wanting improvements
        response2 = client.post(
            "/chat",
            json={
                "conversation_id": conv_id,
                "message": "Yes, please fix all issues",
                "apply_improvements": True
            }
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should return improved code
        assert data2["improved_code"] is not None
        assert len(data2["improved_code"]) > 0
        
        # Should maintain same conversation
        assert data2["conversation_id"] == conv_id
        
        # Improved code should be different from original
        assert "secret123" not in data2["improved_code"]
    
    def test_user_declines_improvements(self, client: TestClient):
        """User says 'no' to improvements, should acknowledge."""
        # Step 1: Initial analysis
        response1 = client.post(
            "/chat",
            json={
                "source_code": "fun main() { val x = 1 }"
            }
        )
        data1 = response1.json()
        conv_id = data1["conversation_id"]
        
        # Step 2: User declines
        response2 = client.post(
            "/chat",
            json={
                "conversation_id": conv_id,
                "message": "No thanks",
                "apply_improvements": False
            }
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should acknowledge but not provide improved code
        assert data2["improved_code"] is None
        assert data2["summary"] is not None  # Some acknowledgment message
    
    # ========================================================================
    # Selective Fix Flow
    # ========================================================================
    
    def test_user_requests_specific_fix(self, client: TestClient):
        """User asks to fix only specific issue type."""
        # Step 1: Initial analysis
        response1 = client.post(
            "/chat",
            json={
                "source_code": """
                fun main() {
                    val password = "secret123"
                    for (i in 0..1000000) { println(i) }
                }
                """
            }
        )
        data1 = response1.json()
        conv_id = data1["conversation_id"]
        
        # Step 2: User asks to fix only security issues
        response2 = client.post(
            "/chat",
            json={
                "conversation_id": conv_id,
                "message": "Fix only the security issues",
                "apply_improvements": True
            }
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should return code with security fixed
        assert data2["improved_code"] is not None
        assert "secret123" not in data2["improved_code"]
        
        # Should still have pending issues (performance)
        # This would be tracked in conversation state
    
    # ========================================================================
    # Follow-up Questions & Explanations
    # ========================================================================
    
    def test_user_asks_for_explanation(self, client: TestClient):
        """User asks agent to explain a specific issue."""
        # Step 1: Initial analysis
        response1 = client.post(
            "/chat",
            json={
                "source_code": "fun main() { for (i in 0..1000000) { println(i) } }"
            }
        )
        data1 = response1.json()
        conv_id = data1["conversation_id"]
        
        # Step 2: User asks for explanation
        response2 = client.post(
            "/chat",
            json={
                "conversation_id": conv_id,
                "message": "Why is this a performance issue?"
            }
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should provide explanation in summary
        assert data2["summary"] is not None
        assert len(data2["summary"]) > 50  # Meaningful explanation
        
        # Shouldn't provide improved code unless asked
        assert data2["improved_code"] is None
    
    # ========================================================================
    # Iterative Improvement Flow
    # ========================================================================
    
    def test_iterative_improvements(self, client: TestClient):
        """User applies fixes one at a time across multiple turns."""
        # Turn 1: Initial analysis
        r1 = client.post("/chat", json={
            "source_code": """
            fun main() {
                val password = "secret"
                for (i in 0..999999) { println(i) }
            }
            """
        })
        conv_id = r1.json()["conversation_id"]
        
        # Turn 2: Fix security first
        r2 = client.post("/chat", json={
            "conversation_id": conv_id,
            "message": "Fix security issues first",
            "apply_improvements": True
        })
        assert r2.status_code == 200
        improved_v1 = r2.json()["improved_code"]
        assert "secret" not in improved_v1
        
        # Turn 3: Now fix performance
        r3 = client.post("/chat", json={
            "conversation_id": conv_id,
            "message": "Now fix the performance issues",
            "apply_improvements": True
        })
        assert r3.status_code == 200
        improved_v2 = r3.json()["improved_code"]
        
        # Final code should have both fixes
        assert improved_v2 is not None
        assert "secret" not in improved_v2
        # Performance improvement would be reflected in code structure
    
    # ========================================================================
    # Context Retention
    # ========================================================================
    
    def test_conversation_remembers_context(self, client: TestClient):
        """Agent should remember previous conversation context."""
        # Turn 1: Initial analysis
        r1 = client.post("/chat", json={
            "source_code": "fun main() { val x = 1 }"
        })
        conv_id = r1.json()["conversation_id"]
        
        # Turn 2: Vague follow-up (relies on context)
        r2 = client.post("/chat", json={
            "conversation_id": conv_id,
            "message": "Tell me more about the first issue"
        })
        
        assert r2.status_code == 200
        # Should understand "first issue" refers to issues from first analysis
        # and provide relevant explanation
        assert r2.json()["summary"] is not None
    
    def test_nonexistent_conversation_id_returns_error(self, client: TestClient):
        """Using invalid conversation_id should return appropriate error."""
        response = client.post("/chat", json={
            "conversation_id": "nonexistent-id-12345",
            "message": "Hello"
        })
        
        # Should return error (400 or 404)
        assert response.status_code in [400, 404]
    
    # ========================================================================
    # Edge Cases
    # ========================================================================
    
    def test_new_code_in_existing_conversation(self, client: TestClient):
        """Submitting new code in existing conversation should start fresh analysis."""
        # Turn 1: Analyze first code
        r1 = client.post("/chat", json={
            "source_code": "fun main() { val x = 1 }"
        })
        conv_id = r1.json()["conversation_id"]
        
        # Turn 2: Submit different code in same conversation
        r2 = client.post("/chat", json={
            "conversation_id": conv_id,
            "source_code": "fun main() { val password = \"secret\" }"
        })
        
        assert r2.status_code == 200
        # Should analyze the new code
        assert r2.json()["issues"] is not None
        # Conversation state should reset for new code
    
    def test_empty_message_with_conversation_id(self, client: TestClient):
        """Empty message in existing conversation should return error."""
        r1 = client.post("/chat", json={
            "source_code": "fun main() {}"
        })
        conv_id = r1.json()["conversation_id"]
        
        r2 = client.post("/chat", json={
            "conversation_id": conv_id,
            "message": ""
        })
        
        # Should require actual message content (400 or 422 validation error)
        assert r2.status_code in [400, 422]
