"""
Asynchronous job management service.
Handles job submission, status, and result storage for code improvement tasks.
"""

import threading
import time
import uuid
from typing import Any, Dict, Optional, Callable, Awaitable

JobRecord = Dict[str, Any]
class JobManager:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = threading.Lock()

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = {"status": "queued", "created_at": time.time()}
        return job_id

    def set_status(self, job_id: str, status: str, **extra: Any) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(status=status, **extra)

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

    def cleanup(self, ttl_seconds: int) -> int:
        now = time.time()
        removed = 0
        with self._lock:
            stale = [jid for jid, rec in self._jobs.items() if now - rec.get("created_at", now) > ttl_seconds]
            for jid in stale:
                self._jobs.pop(jid, None)
                removed += 1
        return removed

    def active_count(self) -> int:
        with self._lock:
            return sum(1 for j in self._jobs.values() if j.get("status") in {"queued", "running"})

    async def run_job(self, job_id: str, coro_factory: Callable[[], Awaitable[Any]]) -> None:
        self.set_status(job_id, "running")
        try:
            result = await coro_factory()
            # If result is None, treat as error
            if result is None:
                self.set_status(job_id, "error", error="No result returned from code review.", completed_at=time.time())
                return
            # If result contains an 'error' field, treat as error
            if isinstance(result, dict) and result.get("error"):
                self.set_status(job_id, "error", error=result.get("summary", "Bedrock error"), completed_at=time.time())
                return
            # If result is an empty dict, treat as success (no issues found)
            stored = result.model_dump() if hasattr(result, "model_dump") else result
            self.set_status(job_id, "done", result=stored, completed_at=time.time())
        except Exception as e:  # pragma: no cover - best-effort logging
            self.set_status(job_id, "error", error=str(e), completed_at=time.time())

    @property
    def jobs(self) -> Dict[str, JobRecord]:
        return self._jobs
