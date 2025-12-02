import pytest
from unittest.mock import MagicMock, patch
from src.crew import CodeReviewProject
import json

class TestCodeReviewProject:

    @pytest.fixture
    def mock_bedrock(self):
        with patch("src.crew.BedrockClient") as MockClient:
            instance = MockClient.return_value
            yield instance

    def test_code_review_success(self, mock_bedrock):
        # Setup mock response
        expected_response = {
            "summary": "Good code",
            "issues": [
                {
                    "type": "SECURITY",
                    "description": "Hardcoded password",
                    "suggestion": "Use env var"
                }
            ]
        }
        mock_bedrock.invoke.return_value = json.dumps(expected_response)

        project = CodeReviewProject()
        result = project.code_review("val password = \"secret\"")

        assert result["summary"] == "Good code"
        assert len(result["issues"]) == 1
        assert result["issues"][0]["type"] == "SECURITY"

    def test_code_review_empty_response(self, mock_bedrock):
        mock_bedrock.invoke.return_value = ""

        project = CodeReviewProject()
        result = project.code_review("val x = 1")

        assert result["error"] == "empty_response"
        assert result["issues"] == []

    def test_code_review_invalid_json(self, mock_bedrock):
        mock_bedrock.invoke.return_value = "Not JSON"

        project = CodeReviewProject()
        result = project.code_review("val x = 1")

        assert result["error"] == "parse_error"

    def test_improve_code_bedrock_success(self, mock_bedrock):
        mock_bedrock.invoke.return_value = "val password = System.getenv(\"PASSWORD\")"

        project = CodeReviewProject()
        issues = [{"type": "SECURITY", "description": "Hardcoded password"}]
        result = project.improve_code("val password = \"secret\"", issues)

        assert result == "val password = System.getenv(\"PASSWORD\")"

    def test_improve_code_fallback_security(self, mock_bedrock):
        # Simulate empty response from Bedrock to trigger fallback
        mock_bedrock.invoke.return_value = ""

        project = CodeReviewProject()
        issues = [
            {
                "type": "SECURITY",
                "description": "Hardcoded password detected",
                "suggestion": "Use env var"
            }
        ]
        
        # Original code with hardcoded password
        original_code = 'val password = "secret123"'
        
        result = project.improve_code(original_code, issues, language="kotlin")

        # Fallback should replace it with System.getenv
        assert 'System.getenv("PASSWORD")' in result
        assert '"secret123"' not in result

    def test_improve_code_fallback_performance(self, mock_bedrock):
        # Simulate empty response from Bedrock to trigger fallback
        mock_bedrock.invoke.return_value = ""

        project = CodeReviewProject()
        issues = [
            {
                "type": "PERFORMANCE",
                "description": "Inefficient loop detected",
                "suggestion": "Remove println"
            }
        ]
        
        # Original code with println in loop
        original_code = """
        fun main() {
            for (i in 0..10) {
                println(i)
            }
        }
        """
        
        result = project.improve_code(original_code, issues, language="kotlin")

        # Fallback should comment out the loop body or remove println
        # The regex in crew.py is: r'for\s*\([^)]*\)\s*\{[^}]*println\([^)]*\)[^}]*\}' -> r'// Optimized loop (println removed)'
        assert "// Optimized loop (println removed)" in result
        assert "println(i)" not in result
