import time
import pytest

from app.services.rate_limiter import RateLimiter
from app.services.job_manager import JobManager
from app.domain.models import ChatResponse


# =========================
# RateLimiter tests
# =========================

def test_rate_limiter_basic_allow_then_limit():
    rl = RateLimiter(limit_per_minute=3)
    ip = "1.2.3.4"

    # First 3 requests allowed
    assert rl.check(ip) is None
    assert rl.check(ip) is None
    assert rl.check(ip) is None

    # 4th should be limited and return retry_after >= 1
    retry_after = rl.check(ip)
    assert isinstance(retry_after, int)
    assert retry_after >= 1

    # Reset clears all buckets
    rl.reset()
    assert rl.check(ip) is None


def test_rate_limiter_window_reset():
    rl = RateLimiter(limit_per_minute=1)
    ip = "5.6.7.8"

    assert rl.check(ip) is None  # first request allowed
    # Simulate window passing
    rl.buckets[ip]["reset"] = time.time() - 1

    # Next request should be allowed again and count reset
    assert rl.check(ip) is None
    assert rl.buckets[ip]["count"] == 1


# =========================
# JobManager tests
# =========================

def test_job_manager_basic_lifecycle():
    jm = JobManager()
    job_id = jm.create_job()

    job = jm.get(job_id)
    assert job is not None
    assert job["status"] == "queued"

    # Active count considers queued/running
    assert jm.active_count() == 1

    jm.set_status(job_id, "running")
    assert jm.active_count() == 1

    jm.set_status(job_id, "done")
    assert jm.active_count() == 0


def test_job_manager_cleanup_removes_stale():
    jm = JobManager()
    job_id = jm.create_job()

    # Make it stale
    jm.jobs[job_id]["created_at"] = time.time() - 7200

    removed = jm.cleanup(ttl_seconds=3600)
    assert removed == 1
    assert jm.get(job_id) is None


def test_job_manager_run_job_success():
    import asyncio
    jm = JobManager()
    job_id = jm.create_job()

    async def make_resp():
        return ChatResponse(summary="ok", issues=[])

    asyncio.run(jm.run_job(job_id, make_resp))

    job = jm.get(job_id)
    assert job is not None
    assert job["status"] == "done"
    assert isinstance(job.get("result"), dict)
    assert job["result"].get("summary") == "ok"
    assert "completed_at" in job


def test_job_manager_run_job_failure():
    import asyncio
    jm = JobManager()
    job_id = jm.create_job()

    async def boom():
        raise RuntimeError("boom")

    asyncio.run(jm.run_job(job_id, boom))

    job = jm.get(job_id)
    assert job is not None
    assert job["status"] == "error"
    assert "boom" in job.get("error", "")
