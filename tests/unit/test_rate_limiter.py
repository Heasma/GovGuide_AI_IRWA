"""
GovGuide AI — Unit Tests: Rate Limiter Middleware
"""

import pytest
from app.middleware.rate_limiter import RateLimiter


def test_rate_limiter_allows_under_limit():
    limiter = RateLimiter(requests_per_minute=5, query_per_minute=3)
    ip = "192.168.1.100"

    for i in range(3):
        allowed, rem = limiter.is_allowed(ip, "/api/v1/query")
        assert allowed is True

    # 4th query should be rejected (limit = 3)
    allowed, rem = limiter.is_allowed(ip, "/api/v1/query")
    assert allowed is False
    assert rem == 0


def test_rate_limiter_different_ips():
    limiter = RateLimiter(requests_per_minute=2, query_per_minute=2)
    ip1 = "10.0.0.1"
    ip2 = "10.0.0.2"

    assert limiter.is_allowed(ip1, "/api/v1/services")[0] is True
    assert limiter.is_allowed(ip1, "/api/v1/services")[0] is True
    assert limiter.is_allowed(ip1, "/api/v1/services")[0] is False

    # ip2 is unaffected
    assert limiter.is_allowed(ip2, "/api/v1/services")[0] is True
