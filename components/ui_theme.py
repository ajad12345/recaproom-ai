"""UI Design System & Styling for RecapRoom AI.
Provides clean CSS styles, hero banners, badges, and card components.
"""
import html
import streamlit as st

CUSTOM_CSS = """
<style>
/* Modern typography and container polish */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

code, pre, .stCodeBlock {
    font-family: 'JetBrains Mono', Consolas, monospace !important;
}

/* Hero Banner */
.recap-hero {
    background: linear-gradient(135deg, rgba(255, 75, 75, 0.08) 0%, rgba(37, 99, 235, 0.08) 100%);
    border: 1px solid rgba(255, 75, 75, 0.2);
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
}

.recap-hero-title {
    font-size: 2.1rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0;
    line-height: 1.2;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.recap-hero-subtitle {
    font-size: 1.05rem;
    opacity: 0.85;
    margin-top: 0.4rem;
    margin-bottom: 0.8rem;
    font-weight: 500;
}

.recap-badge-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.6rem;
}

.recap-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.chip-primary {
    background: rgba(255, 75, 75, 0.12);
    color: #ff4b4b;
    border: 1px solid rgba(255, 75, 75, 0.3);
}

.chip-success {
    background: rgba(16, 185, 129, 0.12);
    color: #059669;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.chip-blue {
    background: rgba(37, 99, 235, 0.12);
    color: #2563eb;
    border: 1px solid rgba(37, 99, 235, 0.3);
}

/* Result Cards */
.result-card {
    background: var(--background-color, #ffffff);
    border: 1px solid rgba(128, 128, 128, 0.2);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.85rem;
    box-shadow: 0 2px 8px -1px rgba(0, 0, 0, 0.04);
    transition: all 0.2s ease-in-out;
}

.result-card:hover {
    border-color: rgba(255, 75, 75, 0.4);
    box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.08);
}

/* Provenance Badges */
.badge-stated {
    background: #059669;
    color: #ffffff !important;
    padding: 2px 9px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.badge-inferred {
    background: #2563eb;
    color: #ffffff !important;
    padding: 2px 9px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.badge-unspecified {
    background: rgba(245, 158, 11, 0.15);
    color: #d97706 !important;
    border: 1px solid rgba(245, 158, 11, 0.4);
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}

.evidence-box {
    margin-top: 0.5rem;
    padding: 0.5rem 0.75rem;
    border-left: 3px solid #059669;
    background: rgba(5, 150, 105, 0.05);
    border-radius: 0 8px 8px 0;
    font-size: 0.86rem;
    color: var(--text-color, #374151);
}

.evidence-loc {
    display: inline-block;
    padding: 1px 6px;
    background: rgba(0, 0, 0, 0.07);
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 6px;
}

/* Sidebar polish */
[data-testid="stSidebar"] {
    border-right: 1px solid rgba(128, 128, 128, 0.15);
}

/* Button enhancements */
.stButton>button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.15s ease;
}

.stButton>button[kind="primary"] {
    box-shadow: 0 2px 10px rgba(255, 75, 75, 0.25);
}
</style>
"""

def inject_custom_theme():
    """Inject modern CSS system into the current Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def render_hero_header():
    """Render the standard top hero header."""
    st.markdown("""
    <div class="recap-hero">
        <div class="recap-hero-title">🎙️ RecapRoom AI</div>
        <div class="recap-hero-subtitle">Lecture and Meeting Summarizer with Grounded Attribution</div>
        <div class="recap-badge-container">
            <span class="recap-chip chip-success">🛡️ Zero Hallucinations</span>
            <span class="recap-chip chip-primary">📍 Line-Level Provenance</span>
            <span class="recap-chip chip-blue">⚖️ Cross-Meeting Diff Tracker</span>
            <span class="recap-chip chip-success">⚡ Map-Reduce Architecture</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
