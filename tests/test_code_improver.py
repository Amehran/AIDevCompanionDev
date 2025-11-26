"""
Tests for Code Improver Agent.

Following TDD: These tests define expected behavior for code improvement agent.
The agent should generate fixed code based on detected issues.
"""

from src.crew import CodeReviewProject



class TestCodeImproverAgent:
    def setup_method(self):
        # Patch BedrockClient.invoke to return improved code for all tests
        from app.bedrock import client as bedrock_client_mod
        self._original_invoke = bedrock_client_mod.BedrockClient.invoke
        def mock_invoke(self, prompt, max_tokens=1024, temperature=0.2):
            # Return code with issues fixed for each test
            if "secret123" in prompt or 'secret' in prompt:
                return prompt.replace('"secret123"', 'System.getenv("PASSWORD")').replace('"secret"', 'System.getenv("PASSWORD")')
            if "hardcoded-api-key" in prompt:
                return prompt.replace('"hardcoded-api-key"', 'System.getenv("API_KEY")')
            if "println(i)" in prompt:
                return prompt.replace('println(i)', '// batched output')
            if "Hello, World!" in prompt:
                return prompt
            return prompt
        bedrock_client_mod.BedrockClient.invoke = mock_invoke
        # Create a fresh CodeReviewProject for each test
        self.project = CodeReviewProject()

    def teardown_method(self):
        # Restore original BedrockClient.invoke
        from app.bedrock import client as bedrock_client_mod
        bedrock_client_mod.BedrockClient.invoke = self._original_invoke
    
    def test_fix_hardcoded_credentials(self):
        """Should replace hardcoded credentials with environment variables."""
        original_code = '''
fun main() {
    val password = "secret123"
    val apiKey = "hardcoded-api-key"
    println("Connecting...")
}
'''
        issues = [
            {
                "type": "SECURITY",
                "description": "Hardcoded credentials detected",
                "suggestion": "Use environment variables"
            }
        ]
        
        improved_code = self.project.improve_code(original_code, issues)
        
        assert improved_code is not None
        assert "secret123" not in improved_code
        assert "hardcoded-api-key" not in improved_code
        # Should use environment variables or config
        assert "getenv" in improved_code.lower() or "env" in improved_code.lower()
    
    def test_fix_performance_issues(self):
        """Should optimize inefficient loops."""
        original_code = '''
fun main() {
    for (i in 0..1000000) {
        println(i)
    }
}
'''
        issues = [
            {
                "type": "PERFORMANCE",
                "description": "Inefficient I/O in loop",
                "suggestion": "Batch output operations"
            }
        ]
        
        improved_code = self.project.improve_code(original_code, issues)
        
        assert improved_code is not None
        # Should not have println inside loop
        assert improved_code != original_code
        # Could use StringBuilder, batch operations, etc.
    
    def test_fix_multiple_issues(self):
        """Should fix multiple types of issues in one pass."""
        original_code = '''
fun main() {
    val password = "secret"
    for (i in 0..1000) {
        println("Password: $password")
    }
}
'''
        issues = [
            {
                "type": "SECURITY",
                "description": "Hardcoded credentials",
                "suggestion": "Use environment variables"
            },
            {
                "type": "PERFORMANCE",
                "description": "I/O in loop",
                "suggestion": "Optimize loop"
            }
        ]
        
        improved_code = self.project.improve_code(original_code, issues)
        
        assert improved_code is not None
        assert "secret" not in improved_code  # Security fixed
        # Performance should be improved (no println in tight loop)
    
    # ========================================================================
    # Selective Improvements
    # ========================================================================
    
    def test_fix_only_security_issues(self):
        """Should fix only security issues when requested."""
        original_code = '''
fun main() {
    val password = "secret"
    for (i in 0..1000) {
        println(i)
    }
}
'''
        issues = [
            {
                "type": "SECURITY",
                "description": "Hardcoded credentials",
                "suggestion": "Use environment variables"
            },
            {
                "type": "PERFORMANCE",
                "description": "I/O in loop",
                "suggestion": "Optimize"
            }
        ]
        
        # Fix only security issues
        improved_code = self.project.improve_code(
            original_code, 
            issues,
            fix_types=["SECURITY"]
        )
        
        assert improved_code is not None
        assert "secret" not in improved_code  # Security fixed
        # Performance issue should remain (println still in loop)
        assert "println" in improved_code
    
    def test_fix_only_performance_issues(self):
        """Should fix only performance issues when requested."""
        original_code = '''
fun main() {
    val password = "secret"
    for (i in 0..1000) {
        println(i)
    }
}
'''
        issues = [
            {
                "type": "SECURITY",
                "description": "Hardcoded credentials",
                "suggestion": "Use environment variables"
            },
            {
                "type": "PERFORMANCE",
                "description": "I/O in loop",
                "suggestion": "Optimize"
            }
        ]
        
        improved_code = self.project.improve_code(
            original_code,
            issues,
            fix_types=["PERFORMANCE"]
        )
        
        assert improved_code is not None
        # Security issue should remain
        assert "secret" in improved_code
        # Performance should be improved
    
    # ========================================================================
    # Context-Aware Improvements
    # ========================================================================
    
    def test_improvement_with_conversation_context(self):
        """Should use conversation context to make better improvements."""
        original_code = '''
fun authenticate(username: String) {
    val password = "secret123"
    // authentication logic
}
'''
        issues = [
            {
                "type": "SECURITY",
                "description": "Hardcoded password",
                "suggestion": "Use secure storage"
            }
        ]
        
        context = {
            "user_preference": "Use Kotlin's getenv",
            "previous_fixes": []
        }
        
        improved_code = self.project.improve_code(
            original_code,
            issues,
            context=context
        )
        
        assert improved_code is not None
        assert "secret123" not in improved_code
        # Should respect user preference for getenv
        assert "getenv" in improved_code.lower() or "System.getenv" in improved_code
    
    def test_preserve_code_structure(self):
        """Should preserve overall code structure and only fix issues."""
        original_code = '''
/**
 * Main entry point
 */
fun main() {
    val password = "secret"
    println("Starting app...")
    connectToDatabase(password)
}

fun connectToDatabase(pwd: String) {
    // connection logic
}
'''
        issues = [
            {
                "type": "SECURITY",
                "description": "Hardcoded password",
                "suggestion": "Use environment variables"
            }
        ]
        
        improved_code = self.project.improve_code(original_code, issues)
        
        assert improved_code is not None
        # Should preserve comments
        assert "Main entry point" in improved_code
        # Should preserve function structure
        assert "fun connectToDatabase" in improved_code
        # Should preserve other statements
        assert "Starting app" in improved_code
        # But fix the issue
        assert "secret" not in improved_code
    
    # ========================================================================
    # Edge Cases
    # ========================================================================
    
    def test_improve_code_with_no_issues(self):
        """Should return original code when no issues to fix."""
        original_code = '''
fun main() {
    println("Hello, World!")
}
'''
        issues = []
        
        improved_code = self.project.improve_code(original_code, issues)
        
        # Should return original or minimally changed code
        assert improved_code is not None
        assert "Hello, World!" in improved_code
    
    def test_handle_invalid_code_gracefully(self):
        """Should handle invalid/malformed code gracefully."""
        invalid_code = "fun main( { invalid syntax"
        issues = [
            {
                "type": "SYNTAX",
                "description": "Invalid syntax",
                "suggestion": "Fix syntax errors"
            }
        ]
        
        # Should not crash
        result = self.project.improve_code(invalid_code, issues)
        assert result is not None
    
    def test_improvement_is_valid_code(self):
        """Improved code should be syntactically valid."""
        original_code = '''
fun main() {
    val password = "secret123"
}
'''
        issues = [
            {
                "type": "SECURITY",
                "description": "Hardcoded credentials",
                "suggestion": "Use environment variables"
            }
        ]
        
        improved_code = self.project.improve_code(original_code, issues)
        
        assert improved_code is not None
        # Basic syntax checks
        assert "fun main()" in improved_code
        assert improved_code.count("{") == improved_code.count("}")
        assert improved_code.count("(") == improved_code.count(")")
    
    # ========================================================================
    # Iterative Improvements
    # ========================================================================
    
    def test_apply_fix_to_already_improved_code(self):
        """Should be able to apply additional fixes to already improved code."""
        # Start with code that has multiple issues
        original_code = '''
fun main() {
    val password = "secret"
    for (i in 0..1000) {
        println("Password: $password, iteration: $i")
    }
}
'''
        
        # First, fix security issue
        security_issues = [
            {
                "type": "SECURITY",
                "description": "Hardcoded credentials",
                "suggestion": "Use environment variables"
            }
        ]
        
        improved_v1 = self.project.improve_code(
            original_code,
            security_issues,
            fix_types=["SECURITY"]
        )
        
        assert "secret" not in improved_v1
        
        # Then, fix performance issue on already-improved code
        performance_issues = [
            {
                "type": "PERFORMANCE",
                "description": "I/O in loop",
                "suggestion": "Optimize"
            }
        ]
        
        improved_v2 = self.project.improve_code(
            improved_v1,
            performance_issues,
            fix_types=["PERFORMANCE"]
        )
        
        assert improved_v2 is not None
        # Both fixes should be present
        assert "secret" not in improved_v2  # Security still fixed
        # Performance improved
    
    # ========================================================================
    # Language Support
    # ========================================================================
    
    def test_improve_python_code(self):
        """Should handle Python code improvements."""
        python_code = '''
def main():
    password = "secret123"
    print(f"Password is {password}")
'''
        issues = [
            {
                "type": "SECURITY",
                "description": "Hardcoded credentials",
                "suggestion": "Use os.getenv"
            }
        ]
        
        improved_code = self.project.improve_code(
            python_code,
            issues,
            language="python"
        )
        
        assert improved_code is not None
        assert "secret123" not in improved_code
        # Should use Python's approach
        assert "os.getenv" in improved_code or "os.environ" in improved_code
    
    def test_improve_java_code(self):
        """Should handle Java code improvements."""
        java_code = '''
public class Main {
    public static void main(String[] args) {
        String password = "secret123";
        System.out.println(password);
    }
}
'''
        issues = [
            {
                "type": "SECURITY",
                "description": "Hardcoded credentials",
                "suggestion": "Use System.getenv"
            }
        ]
        
        improved_code = self.project.improve_code(
            java_code,
            issues,
            language="java"
        )
        
        assert improved_code is not None
        assert "secret123" not in improved_code
        assert "System.getenv" in improved_code
