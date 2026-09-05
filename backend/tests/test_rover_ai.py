"""rover_ai.py testleri — hiçbiri gerçek ağ çağrısı yapmaz.

Odak maliyet kontrolü: anomali sayısı arttığında Groq çağrısı da artıyordu ve
hiçbir üst sınır yoktu. Ayrıca hatalar loglanmadan fallback'e düşüyordu.
"""

import httpx
import pytest

import rover_ai
from rover_ai import _CostGuard, _SlidingWindowLimit, think

CTX = {
    "anomaly_score": 80.0,
    "channel_id": "T-1",
    "sensor_type": "TEMP",
    "raw_value": 0.5,
    "uplink_eligible": True,
}


@pytest.fixture(autouse=True)
def fresh_guard(monkeypatch):
    """Her test kendi kota sayacıyla başlasın."""
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    guard = _CostGuard()
    monkeypatch.setattr(rover_ai, "_guard", guard)
    monkeypatch.setattr(rover_ai, "_BACKOFF_BASE", 0.0)  # testler beklemesin
    return guard


def _stub_transport(handler):
    """httpx isteklerini ağa çıkmadan karşılar."""
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _ok_response(text="Analiz tamam.\nTX"):
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": text}}]},
    )


class TestGating:
    async def test_low_score_never_calls_the_api(self, monkeypatch):
        called = False

        def handler(request):
            nonlocal called
            called = True
            return _ok_response()

        monkeypatch.setattr(rover_ai, "_get_client", lambda: _stub_transport(handler))

        result = await think({**CTX, "anomaly_score": 10.0})

        assert result["model"] == "skipped"
        assert called is False

    async def test_missing_api_key_never_calls_the_api(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        called = False

        def handler(request):
            nonlocal called
            called = True
            return _ok_response()

        monkeypatch.setattr(rover_ai, "_get_client", lambda: _stub_transport(handler))

        result = await think(CTX)

        assert result["model"] == "fallback"
        assert called is False


class TestRateLimiting:
    async def test_calls_beyond_the_minute_limit_are_skipped(
        self, monkeypatch, fresh_guard
    ):
        monkeypatch.setenv("ROVER_THINK_MAX_CALLS_PER_MIN", "3")
        guard = _CostGuard()
        monkeypatch.setattr(rover_ai, "_guard", guard)

        calls = 0

        def handler(request):
            nonlocal calls
            calls += 1
            return _ok_response()

        client = _stub_transport(handler)

        async def _client():
            return client

        monkeypatch.setattr(rover_ai, "_get_client", _client)

        results = [await think(CTX) for _ in range(10)]

        assert calls == 3
        assert sum(1 for r in results if r["model"] == rover_ai.MODEL_ID) == 3
        assert sum(1 for r in results if r["model"] == "rate_limited") == 7

    async def test_rate_limited_calls_still_return_a_decision(self, monkeypatch):
        monkeypatch.setenv("ROVER_THINK_MAX_CALLS_PER_MIN", "0")
        monkeypatch.setattr(rover_ai, "_guard", _CostGuard())

        result = await think(CTX)

        assert result["model"] == "rate_limited"
        assert result["decision"] == "TX"  # uplink_eligible=True

    async def test_hourly_limit_also_applies(self, monkeypatch):
        monkeypatch.setenv("ROVER_THINK_MAX_CALLS_PER_MIN", "100")
        monkeypatch.setenv("ROVER_THINK_MAX_CALLS_PER_HOUR", "2")
        monkeypatch.setattr(rover_ai, "_guard", _CostGuard())

        calls = 0

        def handler(request):
            nonlocal calls
            calls += 1
            return _ok_response()

        client = _stub_transport(handler)

        async def _client():
            return client

        monkeypatch.setattr(rover_ai, "_get_client", _client)

        for _ in range(5):
            await think(CTX)

        assert calls == 2

    def test_sliding_window_frees_capacity_over_time(self):
        limit = _SlidingWindowLimit(60.0, 2, "dakika")

        assert limit.allows(1000.0)
        limit.record(1000.0)
        limit.record(1001.0)
        assert not limit.allows(1002.0)

        # Pencere kaydıktan sonra yeniden yer açılmalı
        assert limit.allows(1062.0)

    def test_zero_limit_blocks_everything(self):
        limit = _SlidingWindowLimit(60.0, 0, "dakika")
        assert not limit.allows(1000.0)


class TestRetryBehaviour:
    async def test_server_error_is_retried_then_succeeds(self, monkeypatch, fresh_guard):
        attempts = 0

        def handler(request):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return httpx.Response(503, text="gecici")
            return _ok_response()

        client = _stub_transport(handler)

        async def _client():
            return client

        monkeypatch.setattr(rover_ai, "_get_client", _client)

        result = await think(CTX)

        assert attempts == 2
        assert result["model"] == rover_ai.MODEL_ID
        assert fresh_guard.retried == 1
        assert fresh_guard.completed == 1

    async def test_rate_limit_response_is_retried(self, monkeypatch, fresh_guard):
        attempts = 0

        def handler(request):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return httpx.Response(429, headers={"Retry-After": "0"})
            return _ok_response()

        client = _stub_transport(handler)

        async def _client():
            return client

        monkeypatch.setattr(rover_ai, "_get_client", _client)

        result = await think(CTX)

        assert result["model"] == rover_ai.MODEL_ID
        assert fresh_guard.retried == 1

    async def test_permanent_error_is_not_retried(self, monkeypatch, fresh_guard, caplog):
        attempts = 0

        def handler(request):
            nonlocal attempts
            attempts += 1
            return httpx.Response(401, text="gecersiz anahtar")

        client = _stub_transport(handler)

        async def _client():
            return client

        monkeypatch.setattr(rover_ai, "_get_client", _client)

        with caplog.at_level("ERROR"):
            result = await think(CTX)

        assert attempts == 1  # 401 tekrar denenmemeli
        assert result["model"] == "fallback"
        assert "kalıcı hatayla" in caplog.text
        assert fresh_guard.failed == 1

    async def test_retries_are_exhausted_and_logged(self, monkeypatch, fresh_guard, caplog):
        def handler(request):
            return httpx.Response(500, text="patladi")

        client = _stub_transport(handler)

        async def _client():
            return client

        monkeypatch.setattr(rover_ai, "_get_client", _client)

        with caplog.at_level("ERROR"):
            result = await think(CTX)

        assert result["model"] == "fallback"
        assert fresh_guard.failed == 1
        assert "tükendi" in caplog.text

    async def test_network_error_is_logged_not_swallowed(
        self, monkeypatch, fresh_guard, caplog
    ):
        def handler(request):
            raise httpx.ConnectError("ag yok")

        client = _stub_transport(handler)

        async def _client():
            return client

        monkeypatch.setattr(rover_ai, "_get_client", _client)

        with caplog.at_level("WARNING"):
            result = await think(CTX)

        assert result["model"] == "fallback"
        assert result["decision"] == "TX"
        assert "Groq" in caplog.text
        assert fresh_guard.failed == 1


class TestDecisionParsing:
    async def test_decision_is_read_from_last_line(self, monkeypatch):
        def handler(request):
            return _ok_response("Skor yuksek.\nDROP")

        client = _stub_transport(handler)

        async def _client():
            return client

        monkeypatch.setattr(rover_ai, "_get_client", _client)

        result = await think(CTX)

        assert result["decision"] == "DROP"

    async def test_unparseable_text_falls_back_to_uplink_decision(self, monkeypatch):
        def handler(request):
            return _ok_response("Belirsiz bir aciklama")

        client = _stub_transport(handler)

        async def _client():
            return client

        monkeypatch.setattr(rover_ai, "_get_client", _client)

        result = await think({**CTX, "uplink_eligible": False})

        assert result["decision"] == "DROP"

    async def test_empty_choices_is_logged_as_failure(self, monkeypatch, fresh_guard, caplog):
        def handler(request):
            return httpx.Response(200, json={"choices": []})

        client = _stub_transport(handler)

        async def _client():
            return client

        monkeypatch.setattr(rover_ai, "_get_client", _client)

        with caplog.at_level("ERROR"):
            result = await think(CTX)

        assert result["model"] == "fallback"
        assert fresh_guard.failed == 1


class TestUsageStats:
    async def test_usage_reports_limits_and_counters(self, monkeypatch, fresh_guard):
        def handler(request):
            return _ok_response()

        client = _stub_transport(handler)

        async def _client():
            return client

        monkeypatch.setattr(rover_ai, "_get_client", _client)

        await think(CTX)
        stats = rover_ai.get_usage_stats()

        assert stats["enabled"] is True
        assert stats["completed"] == 1
        assert stats["per_minute_used"] == 1
        assert stats["per_minute_limit"] > 0

    def test_invalid_env_value_falls_back(self, monkeypatch, caplog):
        monkeypatch.setenv("ROVER_THINK_MAX_CALLS_PER_MIN", "cok")
        with caplog.at_level("WARNING"):
            value = rover_ai._env_int("ROVER_THINK_MAX_CALLS_PER_MIN", 6)
        assert value == 6
