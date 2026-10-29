"""LLM provider calls with timeouts, retries and friendly error mapping (Groq, Gemini, demo)."""
import time

from backend.config import get_api_key, get_model
from backend.utils.logging_utils import get_logger, redact

log = get_logger(__name__)


class LLMError(Exception):
    """Base class for all provider problems (messages are safe to show to users)."""


class MissingKeyError(LLMError):
    pass


class ProviderUnavailableError(LLMError):
    pass


class RateLimitError(LLMError):
    pass


class InvalidResponseError(LLMError):
    pass


def map_provider_error(exc: Exception) -> LLMError:
    text = f"{type(exc).__name__} {exc}".lower()
    if "429" in text or "quota" in text or "resource_exhausted" in text or ("rate" in text and "limit" in text):
        return RateLimitError("The AI provider's rate limit was reached. Wait a minute and try again, or switch to Demo Mode.")
    if any(t in text for t in ("401", "403", "api key", "api_key", "authentication", "permission denied", "invalid_api_key")):
        return MissingKeyError("The AI provider rejected the API key. Check the key in your settings, or switch to Demo Mode.")
    return ProviderUnavailableError("The AI provider is unavailable or timed out. Try again in a moment, or switch to Demo Mode.")


class BaseLLMService:
    mode = "LIVE"
    provider = ""
    model = ""
    max_retries = 2
    timeout = 60

    def _call(self, system: str, user: str) -> str:  # pragma: no cover - implemented by subclasses
        raise NotImplementedError

    def generate(self, system: str, user: str) -> str:
        last: LLMError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return self._call(system, user)
            except LLMError:
                raise
            except Exception as exc:  # provider SDKs raise many different types
                err = map_provider_error(exc)
                log.warning("LLM call failed (attempt %d): %s", attempt + 1, redact(str(exc))[:200])
                if isinstance(err, MissingKeyError):
                    raise err from exc
                last = err
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
        assert last is not None
        raise last


class GroqService(BaseLLMService):
    provider = "groq"

    def __init__(self, api_key: str, model: str):
        self._key, self.model = api_key, model

    def _call(self, system: str, user: str) -> str:
        from groq import Groq  # imported lazily so tests/demo mode don't need the SDK

        client = Groq(api_key=self._key, timeout=self.timeout)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or ""


class GeminiService(BaseLLMService):
    provider = "gemini"

    def __init__(self, api_key: str, model: str):
        self._key, self.model = api_key, model

    def _call(self, system: str, user: str) -> str:
        import google.generativeai as genai

        genai.configure(api_key=self._key)
        model = genai.GenerativeModel(self.model, system_instruction=system)
        resp = model.generate_content(
            user,
            generation_config={"temperature": 0.2, "response_mime_type": "application/json"},
            request_options={"timeout": self.timeout},
        )
        return resp.text or ""


def get_llm_service(provider: str, demo_mode: bool):
    """Return the service to use. Raises MissingKeyError if live mode is requested without a key."""
    if demo_mode or provider == "demo":
        from backend.services.mock_llm import MockLLMService

        return MockLLMService()
    key = get_api_key(provider)
    if not key:
        raise MissingKeyError(
            f"No API key found for {provider}. Add it to .env / Streamlit secrets, or turn on Demo Mode in the sidebar."
        )
    model = get_model(provider)
    return GroqService(key, model) if provider == "groq" else GeminiService(key, model)
