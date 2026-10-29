"""Settings reader: st.secrets -> environment -> .env. API keys are only read here."""
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # local .env (ignored by Git)

PROVIDERS = ("groq", "gemini")
DEFAULT_MODELS = {"groq": "llama-3.3-70b-versatile", "gemini": "gemini-2.0-flash"}
KEY_NAMES = {"groq": "GROQ_API_KEY", "gemini": "GEMINI_API_KEY"}


def get_setting(name, default=None):
    """Read from Streamlit session_state first, then secrets, then environment variables."""
    try:
        if name in st.session_state and st.session_state[name]:
            return str(st.session_state[name])
    except Exception:
        pass
    try:
        value = st.secrets[name]
        if value not in (None, ""):
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


def _is_placeholder(value) -> bool:
    return (not value) or str(value).startswith("replace_with")


def get_provider() -> str:
    p = (get_setting("LLM_PROVIDER", "demo") or "demo").strip().lower()
    return p if p in PROVIDERS or p == "demo" else "demo"


def get_api_key(provider: str) -> str:
    key = get_setting(KEY_NAMES.get(provider, ""), "")
    return "" if _is_placeholder(key) else key


def get_model(provider: str) -> str:
    override = get_setting("MODEL_NAME", "")
    return DEFAULT_MODELS.get(provider, "") if _is_placeholder(override) else override


def provider_status(provider: str | None = None) -> dict:
    """Return {'provider','label','colour'} for the status badge."""
    provider = provider or get_provider()
    if provider == "demo":
        return {"provider": "demo", "label": "DEMO", "colour": "orange"}
    if not get_api_key(provider):
        return {"provider": provider, "label": "KEY MISSING", "colour": "red"}
    return {"provider": provider, "label": "LIVE", "colour": "green"}
