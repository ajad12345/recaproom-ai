import pytest

from backend.services import llm_service
from backend.services.llm_service import (BaseLLMService, MissingKeyError, ProviderUnavailableError, RateLimitError,
                                          get_llm_service, map_provider_error)


class _Boom(BaseLLMService):
    provider, model = "boom", "boom"

    def __init__(self, message):
        self.message, self.calls = message, 0

    def _call(self, system, user):
        self.calls += 1
        raise RuntimeError(self.message)


def test_missing_key_gives_readable_error(monkeypatch):
    """live mode without API key -> MissingKeyError that mentions Demo Mode"""
    monkeypatch.setattr(llm_service, "get_api_key", lambda p: "")
    with pytest.raises(MissingKeyError, match="Demo Mode"):
        get_llm_service("groq", demo_mode=False)


def test_demo_mode_needs_no_key(monkeypatch):
    """demo mode -> works without any key"""
    monkeypatch.setattr(llm_service, "get_api_key", lambda p: "")
    assert get_llm_service("groq", demo_mode=True).mode == "DEMO"


def test_provider_outage_retries_then_friendly_error(monkeypatch):
    """provider returns 503 on every call -> 3 attempts, then ProviderUnavailableError"""
    monkeypatch.setattr(llm_service.time, "sleep", lambda s: None)
    svc = _Boom("503 Service Unavailable")
    with pytest.raises(ProviderUnavailableError):
        svc.generate("s", "u")
    assert svc.calls == 3


def test_rate_limit_mapped(monkeypatch):
    """provider returns 429 -> RateLimitError"""
    monkeypatch.setattr(llm_service.time, "sleep", lambda s: None)
    with pytest.raises(RateLimitError):
        _Boom("Error 429 Too Many Requests").generate("s", "u")


def test_bad_key_not_retried():
    """provider returns 401 invalid api key -> MissingKeyError, single attempt"""
    svc = _Boom("401 invalid_api_key")
    with pytest.raises(MissingKeyError):
        svc.generate("s", "u")
    assert svc.calls == 1


def test_error_mapping_messages_do_not_leak_details():
    """exception text containing a key -> user-facing message does not contain it"""
    err = map_provider_error(RuntimeError("timeout calling with gsk_ABCDEFGHIJKLMNOP"))
    assert "gsk_" not in str(err)
