"""Lightweight crew stub.

This module intentionally avoids importing heavy dependencies (crewai, vector DBs) so
Lambda packaging and test environments remain lean. When the real library is not
available, deterministic JSON is returned so upstream handlers can still function.

In the future we can re-enable full CrewAI behavior via a Lambda layer or container
image without changing calling code.
"""

from __future__ import annotations
from typing import Any, Dict

# Minimal stub: only Crew with deterministic kickoff kept. Removing Agent/Task scaffolding
# keeps package size small while retaining existing call site behavior.

class Crew:  # type: ignore
    def kickoff(self, inputs: Dict[str, Any]):  # Return deterministic JSON string
        code = inputs.get("source_code", "")
        preview = code[:60].replace("\n", " ")
        return (
            '{"summary": "Stub analysis OK", "issues": [], '
            f'"meta": {{"preview": "{preview}", "mode": "stub"}}}}'
        )


class CodeReviewProject:
    """Thin wrapper returning a stub Crew.

    The original class included agent/task construction and model name resolution which
    are removed to keep deployment artifact lean. Restore if real CrewAI integration
    is reintroduced.
    """

    def code_review_crew(self) -> Crew:
        return Crew()
    