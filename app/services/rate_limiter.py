"""Rate limiting service.

Provides per-IP fixed window rate limiting using an in-memory bucket store.
Service abstracts concurrency control and logic from FastAPI endpoint layer.
"""
from __future__ import annotations

import threading
import time
from typing import Dict, Any, Optional

class RateLimiter:
    def __init__(self, limit_per_minute: int) -> None:
        self._limit = limit_per_minute
        self._lock = threading.Lock()
        self._buckets: Dict[str, Dict[str, Any]] = {}

    def check(self, ip: str) -> Optional[int]:
        """Check if IP is rate limited.

        Returns retry_after seconds if limited, else None.
        """
        now = time.time()
        window = 60.0
        with self._lock:
            bucket = self._buckets.get(ip)
            if not bucket:
                self._buckets[ip] = {"count": 1, "reset": now + window}
                return None
            if now > bucket["reset"]:
                bucket["count"], bucket["reset"] = 1, now + window
                return None
            if bucket["count"] >= self._limit:
                return max(1, int(bucket["reset"] - now))
            bucket["count"] += 1
            return None

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()

    @property
    def buckets(self) -> Dict[str, Dict[str, Any]]:
        return self._buckets
