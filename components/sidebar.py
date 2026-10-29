"""Sidebar: output settings, provider selection, Demo Mode toggle and status badge."""
import streamlit as st

from backend.config import KEY_NAMES, PROVIDERS, get_api_key, get_provider, provider_status
from backend.models import SummarySettings

_BADGE = {"green": "🟢", "orange": "🟠", "red": "🔴"}


def render_sidebar() -> SummarySettings:
    sb = st.sidebar
    sb.header("⚙️ Settings")
    length = sb.selectbox("Output length", ["Brief", "Standard", "Detailed"], index=1, key="length")
    fmt = sb.selectbox("Output format", ["Bullet notes", "Narrative paragraphs", "Structured table"], key="fmt")
    ttype = sb.radio("Transcript type", ["Meeting", "Lecture"], horizontal=True, key="ttype")

    sb.divider()
    configured = get_provider()
    provider = sb.selectbox("AI provider", list(PROVIDERS),
                            index=PROVIDERS.index(configured) if configured in PROVIDERS else 0, key="provider")
    live_ready = provider_status(provider)["colour"] == "green"
    demo = sb.toggle("Demo Mode (no API key, offline)", value=not live_ready, key="demo_mode",
                     help="Demo Mode uses simple rules instead of a language model. Output is clearly labelled DEMO.")
    
    if not demo and not get_api_key(provider):
        key_var = KEY_NAMES.get(provider, "")
        user_key = sb.text_input(f"{provider.title()} API Key (Optional)", type="password", key=f"input_{key_var}",
                                 help=f"Paste your {provider} key here if not set in secrets or .env")
        if user_key and user_key.strip():
            st.session_state[key_var] = user_key.strip()
            st.rerun()

    status = provider_status("demo" if demo else provider)
    if status["label"] == "DEMO":
        sb.markdown(f"{_BADGE['orange']} **DEMO MODE**: rule-based sample output")
    elif status["label"] == "LIVE":
        sb.markdown(f"{_BADGE['green']} **LIVE**: {provider}")
    else:
        sb.markdown(f"{_BADGE['red']} **KEY MISSING** for {provider}")
        sb.caption("Add key to `.env` / Streamlit secrets, enter it above, or turn on Demo Mode.")

    sb.divider()
    sb.caption("AI-generated notes can be wrong. Verify important items against the original transcript.")
    return SummarySettings(length=length, fmt=fmt, transcript_type=ttype, provider=provider, demo_mode=demo)
