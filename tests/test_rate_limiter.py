import pytest
import time
import threading
from app.services.rate_limiter import RateLimiter

class TestRateLimiter:
    def test_allow_request_within_limit(self):
        """Should allow requests within the limit."""
        limiter = RateLimiter(limit_per_minute=2)
        ip = "127.0.0.1"
        
        assert limiter.check(ip) is None
        assert limiter.check(ip) is None
        
    def test_block_request_exceeding_limit(self):
        """Should block requests exceeding the limit."""
        limiter = RateLimiter(limit_per_minute=1)
        ip = "127.0.0.1"
        
        assert limiter.check(ip) is None
        retry_after = limiter.check(ip)
        assert retry_after is not None
        assert retry_after > 0
        
    def test_reset_window(self):
        """Should allow requests after window resets."""
        limiter = RateLimiter(limit_per_minute=1)
        ip = "127.0.0.1"
        
        # Mock time to simulate window passing
        original_time = time.time
        current_time = 1000.0
        
        try:
            time.time = lambda: current_time
            assert limiter.check(ip) is None
            assert limiter.check(ip) is not None
            
            # Advance time past window (60s)
            current_time += 61.0
            assert limiter.check(ip) is None
        finally:
            time.time = original_time
            
    def test_multiple_ips(self):
        """Should track limits independently for different IPs."""
        limiter = RateLimiter(limit_per_minute=1)
        ip1 = "127.0.0.1"
        ip2 = "192.168.1.1"
        
        assert limiter.check(ip1) is None
        assert limiter.check(ip1) is not None  # ip1 blocked
        
        assert limiter.check(ip2) is None      # ip2 allowed
        
    def test_reset_buckets(self):
        """Should clear all buckets on reset."""
        limiter = RateLimiter(limit_per_minute=1)
        ip = "127.0.0.1"
        
        limiter.check(ip)
        assert len(limiter.buckets) == 1
        
        limiter.reset()
        assert len(limiter.buckets) == 0
        
    def test_thread_safety(self):
        """Should handle concurrent requests safely."""
        limiter = RateLimiter(limit_per_minute=100)
        ip = "127.0.0.1"
        
        def make_request():
            limiter.check(ip)
            
        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        assert limiter.buckets[ip]["count"] == 10
