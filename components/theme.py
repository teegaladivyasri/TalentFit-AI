"""Theme injection and styling helper."""

import streamlit as st
from pathlib import Path
from utils.constants import ThemeMode


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSS_PATH = PROJECT_ROOT / "assets" / "style.css"


def apply_theme() -> None:
    """Read style.css, apply current theme variable mappings, and inject into Streamlit."""
    css_path = DEFAULT_CSS_PATH
    if not css_path.exists():
        css_path = Path("assets/style.css")
    current_theme = st.session_state.get("theme", ThemeMode.LIGHT)
    
    if css_path.exists():
        css_content = css_path.read_text(encoding="utf-8")
        
        # Inject CSS along with explicit theme variable overrides on .stApp for instant CSS rendering
        theme_override = ""
        if current_theme == ThemeMode.DARK:
            theme_override = """
            .stApp, [data-testid="stAppViewContainer"], section.main, .block-container, body, html {
                --bg-app: #0b0f19 !important;
                --bg-surface: #111827 !important;
                --bg-surface-alt: #1a2234 !important;
                --bg-surface-hover: #1f293d !important;
                --border-subtle: #242f44 !important;
                --border-strong: #374151 !important;
                --text-primary: #f9fafb !important;
                --text-secondary: #cbd5e1 !important;
                --text-muted: #94a3b8 !important;
                --tag-matched-bg: #064e3b !important;
                --tag-matched-border: #047857 !important;
                --tag-matched-text: #6ee7b7 !important;
                --tag-missing-bg: #881337 !important;
                --tag-missing-border: #be123c !important;
                --tag-missing-text: #fecdd3 !important;
                --tag-neutral-bg: #1e293b !important;
                --tag-neutral-border: #334155 !important;
                --tag-neutral-text: #cbd5e1 !important;
                --tag-good-bg: #064e3b !important;
                --tag-good-text: #6ee7b7 !important;
                --tag-good-border: #047857 !important;
                --tag-warn-bg: #78350f !important;
                --tag-warn-text: #fde68a !important;
                --tag-warn-border: #92400e !important;
                --tag-bad-bg: #881337 !important;
                --tag-bad-text: #fecdd3 !important;
                --tag-bad-border: #be123c !important;
                --btn-bg: #1f293d !important;
                --btn-text: #f9fafb !important;
                --btn-border: #374151 !important;
                --btn-hover-bg: #27354f !important;
                --btn-hover-border: #60a5fa !important;
                --card-bg: #111827 !important;
                --card-border: #242f44 !important;
                background-color: #0b0f19 !important;
                color: #f9fafb !important;
            }
            """
        else:
            theme_override = """
            .stApp, [data-testid="stAppViewContainer"], section.main, .block-container, body, html {
                --bg-app: #f8fafc !important;
                --bg-surface: #ffffff !important;
                --bg-surface-alt: #f1f5f9 !important;
                --bg-surface-hover: #e2e8f0 !important;
                --border-subtle: #e2e8f0 !important;
                --border-strong: #cbd5e1 !important;
                --text-primary: #0f172a !important;
                --text-secondary: #475569 !important;
                --text-muted: #64748b !important;
                --tag-matched-bg: #ecfdf5 !important;
                --tag-matched-border: #a7f3d0 !important;
                --tag-matched-text: #065f46 !important;
                --tag-missing-bg: #fff1f2 !important;
                --tag-missing-border: #fecdd3 !important;
                --tag-missing-text: #9f1239 !important;
                --tag-neutral-bg: #f1f5f9 !important;
                --tag-neutral-border: #e2e8f0 !important;
                --tag-neutral-text: #334155 !important;
                --tag-good-bg: #ecfdf5 !important;
                --tag-good-text: #065f46 !important;
                --tag-good-border: #a7f3d0 !important;
                --tag-warn-bg: #fef3c7 !important;
                --tag-warn-text: #92400e !important;
                --tag-warn-border: #fde68a !important;
                --tag-bad-bg: #fff1f2 !important;
                --tag-bad-text: #9f1239 !important;
                --tag-bad-border: #fecdd3 !important;
                --btn-bg: #ffffff !important;
                --btn-text: #0f172a !important;
                --btn-border: #cbd5e1 !important;
                --btn-hover-bg: #f8fafc !important;
                --btn-hover-border: #2563eb !important;
                --card-bg: #ffffff !important;
                --card-border: #e2e8f0 !important;
                background-color: #f8fafc !important;
                color: #0f172a !important;
            }
            """

        html_payload = f"""
        <style>
        {css_content}
        {theme_override}
        </style>
        """
        st.markdown(html_payload, unsafe_allow_html=True)
