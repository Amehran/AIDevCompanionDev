import os
from crewai import Agent, Task, Crew


class CodeReviewProject:
    """Android-focused review + JSON formatting crew (compatible with installed CrewAI).

    Agents:
      - code_reviewer_agent: Senior Android Code Quality Analyst
      - json_formatter_agent: JSON Formatting Specialist

    Tasks:
      - code_review_task: analyze Kotlin/Compose source and produce structured findings
      - json_formatter_task: validate/format the analysis into strict JSON
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
        review = self.code_review_task()
        format_json = self.json_formatter_task(review)
        return Crew(
            name="CodeReviewCrew",
            agents=[self.code_reviewer_agent(), self.json_formatter_agent()],
            tasks=[review, format_json],
        )
    