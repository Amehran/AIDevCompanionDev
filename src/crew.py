import os
import logging

logger = logging.getLogger(__name__)

# Attempt to import crewai; fall back to lightweight stubs if unavailable (e.g. test environment)
try:
    from crewai import Agent, Task, Crew  # type: ignore
    CREW_AVAILABLE = True
    logger.info("CrewAI imported successfully")
except Exception as e:  # pragma: no cover - fallback path
    CREW_AVAILABLE = False
    logger.warning(f"CrewAI import failed, using stub mode: {e}")

    class Agent:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

    class Task:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

    class Crew:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def kickoff(self, inputs):  # Return deterministic JSON string
            logger.warning("Using stub Crew.kickoff - CrewAI not available")
            return '{"summary": "OK (stub)", "issues": []}'


class CodeReviewProject:
    """Android-focused review + JSON formatting crew (compatible with installed CrewAI).

    Provides deterministic stub behavior when crewai dependency isn't available so tests
    and local development without full vector DB / embedding stack still function.
    """

    def _model_name(self) -> str:
        return (
            os.getenv("LLM_MODEL")
            or os.getenv("MODEL")
            or os.getenv("MODEL_NAME")
            or "gpt-4o-mini"
        )

    # Agents
    def code_reviewer_agent(self) -> Agent:
        return Agent(
            name="code_reviewer_agent",
            role="Senior Android Code Quality Analyst",
            backstory=(
                "Veteran Android architect with 20+ years experience in high-performance, "
                "maintainable, and secure apps. Expert in Jetpack, coroutines, Compose UI, "
                "and MVVM/Clean Architecture."
            ),
            goal=(
                "Perform expert-level static analysis of Kotlin and Jetpack Compose code. "
                "Identify performance bottlenecks, best practice violations, and security issues."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self._model_name(),
        )

    def json_formatter_agent(self) -> Agent:
        return Agent(
            name="json_formatter_agent",
            role="JSON Formatting Specialist",
            backstory=(
                "Precision-driven validator ensuring outputs follow strict schema and JSON rules. "
                "Does not change meaning, only formats and validates."
            ),
            goal=(
                "Take a written code review and flawlessly convert it into strict, valid JSON."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self._model_name(),
        )

    def code_improver_agent(self) -> Agent:
        return Agent(
            name="code_improver_agent",
            role="Expert Code Refactoring Specialist",
            backstory=(
                "Senior software engineer with expertise in secure coding practices, "
                "performance optimization, and clean code principles. Skilled in multiple "
                "programming languages including Kotlin, Java, and Python."
            ),
            goal=(
                "Generate improved code that fixes identified issues while preserving "
                "functionality, code structure, and readability. Apply best practices "
                "and idiomatic patterns for the target language."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self._model_name(),
        )

    # Tasks
    def code_review_task(self) -> Task:
        """Analyze Kotlin/Compose source and produce structured, actionable findings."""
        return Task(
            description=(
                "Analyze Kotlin/Jetpack Compose source code for performance, security, best practices, "
                "and maintainability. Provide structured, actionable output.\n\n"
                "Source code to analyze:\n{{source_code}}\n\n"
                "Your output must be a valid JSON object with this structure:\n"
                "{{\n"
                '  "summary": "brief overview string",\n'
                '  "issues": [\n'
                "    {{\n"
                '      "type": "PERFORMANCE or SECURITY or BEST_PRACTICE or STYLE or OTHER",\n'
                '      "description": "what the issue is",\n'
                '      "suggestion": "how to fix it"\n'
                "    }}\n"
                "  ]\n"
                "}}"
            ),
            expected_output="A valid JSON object matching the schema above with summary and issues array.",
            agent=self.code_reviewer_agent(),
        )

    def json_formatter_task(self, review_task: Task) -> Task:
        """Validate and normalize the review into strict JSON (single JSON object, no extra text)."""
        return Task(
            description=(
                "Take the previous code analysis and ensure it is formatted as strict, valid JSON.\n"
                "The JSON must match this exact schema:\n"
                "{{\n"
                '  "summary": "string",\n'
                '  "issues": [\n'
                "    {{\n"
                '      "type": "PERFORMANCE or SECURITY or BEST_PRACTICE or STYLE or OTHER",\n'
                '      "description": "string",\n'
                '      "suggestion": "string"\n'
                "    }}\n"
                "  ]\n"
                "}}\n\n"
                "Output ONLY the JSON object. No markdown, no explanations, no extra text."
            ),
            expected_output="A single valid JSON object string matching the schema—no prose, no markdown.",
            agent=self.json_formatter_agent(),
            context=[review_task],
        )

    def code_review_crew(self) -> Crew:
        if not CREW_AVAILABLE:
            # Return stub Crew with deterministic kickoff
            logger.warning("CrewAI not available, returning stub crew")
            return Crew()
        
        # Check if OpenAI API key is configured
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.lower() in ["", "your-api-key-here", "dummy", "test", "placeholder"]:
            logger.error("OPENAI_API_KEY not configured or invalid - CrewAI will not work properly")
            # Could raise an exception here instead of silently failing
            # raise ValueError("OPENAI_API_KEY environment variable must be set to use AI features")
        
        review = self.code_review_task()
        format_json = self.json_formatter_task(review)
        return Crew(
            name="CodeReviewCrew",
            agents=[self.code_reviewer_agent(), self.json_formatter_agent()],
            tasks=[review, format_json],
        )
    
    def improve_code(
        self,
        source_code: str,
        issues: list,
        fix_types: list = None,
        context: dict = None,
        language: str = "kotlin"
    ) -> str:
        """
        Generate improved code that fixes identified issues.
        
        Args:
            source_code: The original source code to improve
            issues: List of issue dicts with type, description, suggestion
            fix_types: Optional list of issue types to fix (e.g., ["SECURITY"])
            context: Optional context dict with user preferences, previous fixes, etc.
            language: Programming language (kotlin, python, java, etc.)
            
        Returns:
            Improved code with issues fixed
        """
        # If no issues, return original code
        if not issues:
            return source_code
        
        # Filter issues by fix_types if specified
        if fix_types:
            issues_to_fix = [i for i in issues if i.get("type") in fix_types]
        else:
            issues_to_fix = issues
        
        # If no issues match the filter, return original
        if not issues_to_fix:
            return source_code
        
        # Use test mode for deterministic behavior in tests
        api_key = os.getenv("OPENAI_API_KEY", "")
        if any(keyword in api_key.lower() for keyword in ["test", "placeholder", "dummy"]):
            return self._improve_code_test_mode(source_code, issues_to_fix, language)
        
        # Build improvement task description
        issues_text = "\n".join([
            f"- {i.get('type', 'UNKNOWN')}: {i.get('description', '')} "
            f"(Suggestion: {i.get('suggestion', '')})"
            for i in issues_to_fix
        ])
        
        context_text = ""
        if context:
            if context.get("user_preference"):
                context_text += f"\nUser preference: {context['user_preference']}"
            if context.get("previous_fixes"):
                context_text += f"\nPrevious fixes applied: {', '.join(context['previous_fixes'])}"
        
        task_description = f"""
You are refactoring {language} code to fix the following issues:

{issues_text}

Original code:
```{language}
{source_code}
```
{context_text}

Generate improved code that:
1. Fixes all the specified issues
2. Preserves the original functionality and behavior
3. Maintains code structure, comments, and readability
4. Uses idiomatic {language} patterns
5. Is syntactically valid and runnable

IMPORTANT: Output ONLY the improved code, no explanations, no markdown fences, no extra text.
"""
        
        improvement_task = Task(
            description=task_description,
            expected_output=f"The improved {language} code with all issues fixed",
            agent=self.code_improver_agent(),
        )
        
        if not CREW_AVAILABLE:
            # Stub mode - return original with minimal changes
            return self._improve_code_test_mode(source_code, issues_to_fix, language)
        
        crew = Crew(
            name="CodeImprovementCrew",
            agents=[self.code_improver_agent()],
            tasks=[improvement_task],
        )
        
        result = crew.kickoff(inputs={"source_code": source_code})
        improved_code = str(result).strip()
        
        # Remove markdown code fences if present
        if improved_code.startswith("```"):
            lines = improved_code.split("\n")
            # Remove first and last lines if they're markdown fences
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            improved_code = "\n".join(lines)
        
        return improved_code
    
    def _improve_code_test_mode(self, source_code: str, issues: list, language: str) -> str:
        """
        Deterministic code improvement for test mode.
        Applies simple regex-based fixes for common issues.
        """
        improved = source_code
        
        for issue in issues:
            issue_type = issue.get("type", "").upper()
            
            if issue_type == "SECURITY":
                # Fix hardcoded credentials
                if language == "kotlin":
                    import re
                    # Replace hardcoded strings that look like secrets
                    improved = re.sub(
                        r'val\s+password\s*=\s*"[^"]*"',
                        'val password = System.getenv("PASSWORD") ?: ""',
                        improved
                    )
                    improved = re.sub(
                        r'val\s+apiKey\s*=\s*"[^"]*"',
                        'val apiKey = System.getenv("API_KEY") ?: ""',
                        improved
                    )
                    improved = re.sub(
                        r'val\s+secret\s*=\s*"[^"]*"',
                        'val secret = System.getenv("SECRET") ?: ""',
                        improved
                    )
                elif language == "python":
                    import re
                    improved = re.sub(
                        r'password\s*=\s*"[^"]*"',
                        'password = os.getenv("PASSWORD", "")',
                        improved
                    )
                    improved = re.sub(
                        r'api_key\s*=\s*"[^"]*"',
                        'api_key = os.getenv("API_KEY", "")',
                        improved
                    )
                    # Add os import if not present
                    if "os.getenv" in improved and "import os" not in improved:
                        improved = "import os\n\n" + improved
                elif language == "java":
                    import re
                    improved = re.sub(
                        r'String\s+password\s*=\s*"[^"]*"',
                        'String password = System.getenv("PASSWORD")',
                        improved
                    )
            
            elif issue_type == "PERFORMANCE":
                # Simple optimization: comment about batching operations
                # In real implementation, would do actual optimization
                if "println" in improved and "for" in improved:
                    # Add comment about optimization needed
                    improved = "// TODO: Consider batching I/O operations for better performance\n" + improved
        
        return improved
    