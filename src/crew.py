import logging
from app.bedrock.client import BedrockClient
import json
logger = logging.getLogger(__name__)


class CodeReviewProject:
    """Android-focused review + JSON formatting crew (compatible with installed CrewAI).

    Provides deterministic stub behavior when crewai dependency isn't available so tests
    and local development without full vector DB / embedding stack still function.
    """

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

    
    def improve_code(self, source_code: str, issues: list, language: str = "kotlin") -> str:
        """
        Use Bedrock Claude to generate improved code based on issues.
        """
        issues_text = json.dumps(issues, indent=2)
        prompt = (
            f"\n\nHuman: Original code (language: {language}):\n{source_code}\n\n"
            f"Issues to fix:\n{issues_text}\n\n"
            "Generate improved code that fixes all the issues, preserves functionality, maintains structure, and uses idiomatic patterns. Output ONLY the improved code, no explanations, no markdown fences, no extra text."
        )
        response = self.bedrock.invoke(prompt + "\n\nAssistant:")
        return response
    
    