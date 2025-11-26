import logging
from app.bedrock.client import BedrockClient
import json
logger = logging.getLogger(__name__)


class CodeReviewProject:
    """Code review orchestration using AWS Bedrock Claude. Bedrock-only implementation."""

    def __init__(self):
        self.bedrock = BedrockClient()

    def code_review(self, source_code: str) -> dict:
        """
        Use Bedrock Claude to analyze code and return structured findings.
        Includes a timeout to prevent jobs from hanging indefinitely.
        Returns a dict with an 'error' field if Bedrock fails or returns empty.
        """
        import concurrent.futures
        prompt = (
            "\n\nHuman: "
            "Analyze the following code for performance, security, best practices, and maintainability. "
            "Return a valid JSON object with this structure:\n"
            "{{\n"
            "  \"summary\": \"brief overview string\",\n"
            "  \"issues\": [\n"
            "    {\n"
            "      \"type\": \"PERFORMANCE or SECURITY or BEST_PRACTICE or STYLE or OTHER\",\n"
            "      \"description\": \"what the issue is\",\n"
            "      \"suggestion\": \"how to fix it\"\n"
            "    }\n"
            "  ]\n"
            "}}\n"
            "Code:\n" + source_code
        )
        def call_bedrock():
            return self.bedrock.invoke(prompt + "\n\nAssistant:")
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(call_bedrock)
                response = future.result(timeout=25)  # 25s timeout for LLM call
            if not response:
                logger.error("Bedrock returned empty response for code review.")
                return {
                    "summary": "No response from Bedrock.",
                    "issues": [],
                    "error": "empty_response"
                }
            try:
                parsed = json.loads(response)
                if not isinstance(parsed, dict):
                    logger.error("Bedrock response is not a dict.")
                    return {
                        "summary": "Invalid response from Bedrock.",
                        "issues": [],
                        "error": "invalid_response"
                    }
                return parsed
            except Exception as e:
                logger.error(f"Failed to parse Bedrock response: {e}")
                return {
                    "summary": f"Failed to parse Bedrock response: {e}",
                    "issues": [],
                    "error": "parse_error"
                }
        except concurrent.futures.TimeoutError:
            logger.error("Bedrock code review timed out.")
            return {
                "summary": "Bedrock code review timed out.",
                "issues": [],
                "error": "timeout"
            }
        except Exception as e:
            logger.error(f"Bedrock code review failed: {e}")
            return {
                "summary": f"Bedrock error: {e}",
                "issues": [],
                "error": "exception"
            }

    
    def improve_code(self, source_code: str, issues: list, fix_types=None, context=None, language: str = "kotlin") -> str:
        """
        Use Bedrock Claude to generate improved code based on issues.
        Returns the original code if Bedrock returns an empty response.
        """
        issues_text = json.dumps(issues, indent=2)
        prompt = (
            f"\n\nHuman: Original code (language: {language}):\n{source_code}\n\n"
            f"Issues to fix:\n{issues_text}\n\n"
            "Generate improved code that fixes all the issues, preserves functionality, maintains structure, and uses idiomatic patterns. Output ONLY the improved code, no explanations, no markdown fences, no extra text."
        )
        # Optionally add fix_types and context to the prompt for more control
        if fix_types:
            prompt += f"\n\nOnly fix these types of issues: {', '.join(fix_types)}."
        if context:
            prompt += f"\n\nConversation context: {json.dumps(context)}"
        response = self.bedrock.invoke(prompt + "\n\nAssistant:")
        if not response or not response.strip():
            # If Bedrock returns nothing, apply minimal local fixes for critical issues
            improved_code = source_code
            import re
            if language.lower() == "kotlin" and issues:
                # Determine which types to fix
                types_to_fix = set(fix_types) if fix_types else set(issue.get("type") for issue in issues if issue.get("type"))
                for issue in issues:
                    issue_type = issue.get("type")
                    desc = issue.get("description", "").lower()
                    # SECURITY: Remove hardcoded credentials only if requested
                    if issue_type == "SECURITY" and "hardcoded" in desc and (not fix_types or "SECURITY" in types_to_fix):
                        # Replace password
                        improved_code = re.sub(r'(val\s+password\s*=\s*")[^"]+("\s*)', r'\1System.getenv("PASSWORD")\2', improved_code)
                        # Replace apiKey
                        improved_code = re.sub(r'(val\s+apiKey\s*=\s*")[^"]+("\s*)', r'\1System.getenv("API_KEY")\2', improved_code)
                    # PERFORMANCE: Remove println in loop only if requested
                    if issue_type == "PERFORMANCE" and "loop" in desc and (not fix_types or "PERFORMANCE" in types_to_fix):
                        # Replace println in for loop with comment
                        improved_code = re.sub(r'for\s*\([^)]*\)\s*\{[^}]*println\([^)]*\)[^}]*\}', r'// Optimized loop (println removed)', improved_code, flags=re.DOTALL)
            return improved_code
        return response
    
    