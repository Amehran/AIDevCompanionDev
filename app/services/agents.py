import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
from app.bedrock.client import BedrockClient
from app.domain.models import Issue

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, name: str, role: str, model_id: Optional[str] = None):
        self.name = name
        self.role = role
        self.client = BedrockClient(model_id=model_id)

    async def analyze(self, code: str) -> Dict[str, Any]:
        prompt = f"""
You are an expert {self.role}. Analyze the following Kotlin code.
Focus ONLY on your area of expertise.

Code:
```kotlin
{code}
```

Return a JSON object with the following structure:
{{
    "summary": "Brief summary of findings from your perspective",
    "issues": [
        {{
            "type": "issue_type",
            "description": "Description of the issue",
            "suggestion": "How to fix it"
        }}
    ]
}}
"""
        try:
            # We run this in a thread pool to avoid blocking the event loop
            # since BedrockClient is synchronous (boto3)
            response = await asyncio.to_thread(self.client.invoke, prompt)
            
            # Parse JSON from response (handling potential markdown wrapping)
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Agent {self.name} failed: {e}")
            return {"summary": f"Agent failed: {e}", "issues": []}

class KotlinAnalysisSwarm:
    def __init__(self):
        self.syntax_agent = Agent("SyntaxAgent", "Kotlin Syntax and Idioms Expert")
        self.security_agent = Agent("SecurityAgent", "Application Security Expert specializing in Android/Kotlin")
        self.performance_agent = Agent("PerformanceAgent", "Android Performance Optimization Expert")
        self.orchestrator = Agent("Orchestrator", "Technical Lead")

    async def analyze(self, code: str) -> Dict[str, Any]:
        # Run specialized agents in parallel
        results = await asyncio.gather(
            self.syntax_agent.analyze(code),
            self.security_agent.analyze(code),
            self.performance_agent.analyze(code)
        )

        syntax_result, security_result, performance_result = results

        # Orchestrator synthesizes the results
        synthesis_prompt = f"""
You are a Technical Lead. Synthesize the following analysis results into a cohesive report for the developer.

Syntax Analysis:
{json.dumps(syntax_result)}

Security Analysis:
{json.dumps(security_result)}

Performance Analysis:
{json.dumps(performance_result)}

Return a FINAL JSON object with this structure:
{{
    "summary": "A comprehensive, encouraging, and professional summary of the code quality.",
    "issues": [
        // Combine and deduplicate issues from the analyses above.
        // Prioritize critical security and performance issues.
    ]
}}
"""
        try:
            final_response = await asyncio.to_thread(self.orchestrator.client.invoke, synthesis_prompt)
             # Parse JSON from response
            json_str = final_response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            # Fallback: simple combination
            all_issues = []
            for res in results:
                if "issues" in res:
                    all_issues.extend(res["issues"])
            return {
                "summary": "Analysis completed (Orchestrator unavailable).",
                "issues": all_issues
            }
