"""Reusable UI Card, Badge, Callout, and SaaS Highlights Components."""

import streamlit as st
from typing import List, Optional, Dict, Any


def render_metric_card(
    label: str, 
    value: str, 
    subtext: str = "", 
    color: Optional[str] = None
) -> None:
    """Render a clean SaaS metric tile with uniform height and clear typography."""
    val_style = f"color: {color};" if color else "color: var(--text-primary);"
    subtext_line = f'<div class="tf-metric-subtext">{subtext}</div>' if subtext else ''
    html = f'<div class="tf-metric-tile"><div class="tf-metric-label">{label}</div><div class="tf-metric-value" style="{val_style}">{value}</div>{subtext_line}</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_skill_badges(
    skills: List[str], 
    badge_type: str = "matched",
    empty_label: str = "None specified"
) -> None:
    """Render a collection of skill chips (matched, missing, neutral, good, warn, or bad)."""
    if not skills:
        st.markdown(f"<span style='color: var(--text-muted); font-size: 0.85rem;'>{empty_label}</span>", unsafe_allow_html=True)
        return

    type_class = {
        "matched": "tf-tag-matched",
        "missing": "tf-tag-missing",
        "neutral": "tf-tag-neutral",
        "good": "tf-tag-good",
        "warn": "tf-tag-warn",
        "bad": "tf-tag-bad",
    }.get(badge_type, "tf-tag-neutral")

    tags_html = "".join([f'<span class="tf-tag {type_class}">{skill}</span>' for skill in skills])
    html = f'<div class="tf-tag-container">{tags_html}</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_callout(text: str, kind: str = "info") -> None:
    """Render a clean information, warning, or success callout strip."""
    cls_map = {
        "info": "tf-callout",
        "warning": "tf-callout tf-callout-warning",
        "success": "tf-callout tf-callout-success"
    }
    cls = cls_map.get(kind, "tf-callout")
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)


def render_hero_preview_mockup() -> None:
    """Render a clean SaaS feature & value highlights card."""
    html = (
        '<div class="tf-card" style="box-shadow: var(--shadow-md); border-radius: var(--radius-lg); padding: 1.5rem; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">'
        '<div>'
        '<div style="font-size: 0.72rem; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">'
        'TalentFit AI Intelligence'
        '</div>'
        '<div style="font-size: 1.2rem; font-weight: 700; color: var(--text-primary); margin-bottom: 1.15rem; letter-spacing: -0.02em;">'
        'Precision Resume & Role Benchmarking'
        '</div>'
        '<div style="display: flex; flex-direction: column; gap: 0.75rem;">'
        '<div style="display: flex; align-items: flex-start; gap: 0.75rem; background-color: var(--bg-surface-alt); padding: 0.75rem 0.9rem; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">'
        '<div style="font-size: 1.1rem; line-height: 1;">🎯</div>'
        '<div>'
        '<div style="font-weight: 600; font-size: 0.85rem; color: var(--text-primary);">JD Match Ratio</div>'
        '<div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 2px;">Direct calculation based on matched skills vs total role requirements.</div>'
        '</div>'
        '</div>'
        '<div style="display: flex; align-items: flex-start; gap: 0.75rem; background-color: var(--bg-surface-alt); padding: 0.75rem 0.9rem; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">'
        '<div style="font-size: 1.1rem; line-height: 1;">💡</div>'
        '<div>'
        '<div style="font-weight: 600; font-size: 0.85rem; color: var(--text-primary);">Actionable Career Guidance</div>'
        '<div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 2px;">Concrete suggestions for resume wording and practical skills to learn.</div>'
        '</div>'
        '</div>'
        '<div style="display: flex; align-items: flex-start; gap: 0.75rem; background-color: var(--bg-surface-alt); padding: 0.75rem 0.9rem; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">'
        '<div style="font-size: 1.1rem; line-height: 1;">⚡</div>'
        '<div>'
        '<div style="font-weight: 600; font-size: 0.85rem; color: var(--text-primary);">Batch Recruiter Screening</div>'
        '<div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 2px;">Deterministic candidate ranking and side-by-side comparison.</div>'
        '</div>'
        '</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
