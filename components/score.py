"""Score visualization, match banners, and status badges."""

import textwrap
import streamlit as st
from typing import Dict, Any
from utils.constants import SkillPriority, CandidateStatus


def get_score_color(score: float) -> str:
    """Return semantic hex color based on score threshold."""
    if score >= 85:
        return "#10B981"  # Emerald
    elif score >= 70:
        return "#2563EB"  # Primary Blue
    elif score >= 55:
        return "#F59E0B"  # Amber
    return "#EF4444"      # Rose


def render_overall_match_banner(
    score: float, 
    role_title: str, 
    candidate_name: str = ""
) -> None:
    """Render high-level prominent match score hero banner."""
    color = get_score_color(score)
    cand_line = f'<div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 4px;">{candidate_name}</div>' if candidate_name else ''
    html = textwrap.dedent(f"""
    <div class="tf-score-banner">
        <div>
            <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">
                MATCH COMPATIBILITY REPORT
            </div>
            <div style="font-size: 1.35rem; font-weight: 700; color: var(--text-primary); margin-top: 3px;">
                {role_title}
            </div>
            {cand_line}
        </div>
        <div style="text-align: right;">
            <div style="font-size: 2.4rem; font-weight: 800; color: {color}; line-height: 1; letter-spacing: -0.02em;">
                {score}%
            </div>
            <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-muted); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.04em;">
                JD Match
            </div>
        </div>
    </div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def render_score_bar(label: str, score: float, description: str = "") -> None:
    """Render a progress bar with percentage label."""
    color = get_score_color(score)
    desc_line = f'<div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 3px;">{description}</div>' if description else ''
    html = textwrap.dedent(f"""
    <div style="margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-size: 0.85rem; font-weight: 600; color: var(--text-primary);">{label}</span>
            <span style="font-size: 0.9rem; font-weight: 700; color: {color};">{score}%</span>
        </div>
        <div style="background-color: var(--bg-surface-alt); height: 8px; border-radius: 4px; overflow: hidden; border: 1px solid var(--border-subtle);">
            <div style="width: {score}%; background-color: {color}; height: 100%; border-radius: 3px;"></div>
        </div>
        {desc_line}
    </div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def render_ats_breakdown(ats_dict: Dict[str, Any]) -> None:
    """Render the ATS Compatibility breakdown panel for recruiter views."""
    rows_html = ""
    label_map = {
        "keyword_coverage": "Keyword Coverage",
        "section_completeness": "Section Completeness",
        "formatting_readability": "Formatting & Layout Readability",
        "terminology_relevance": "Industry Terminology Relevance",
        "text_extractability": "Text Extractability",
        "section_structure": "Section Structure",
        "contact_information": "Contact Details",
        "skill_visibility": "Skill Visibility",
        "content_organization": "Content Organization",
    }
    
    for key, info in ats_dict.items():
        title = label_map.get(key, key.replace("_", " ").title())
        if isinstance(info, dict):
            score = info.get("score", 0)
            detail = info.get("detail", "")
            status = info.get("status", "Good")
        else:
            score = int(info) if isinstance(info, (int, float)) else 80
            detail = f"{title} evaluated against ATS standards."
            status = "Optimal" if score >= 85 else ("Good" if score >= 70 else "Review")
            
        score_color = get_score_color(score)
        
        row_block = f"""<div class="tf-ats-row"><div><div class="tf-ats-label">{title} <span style="font-size: 0.72rem; color: {score_color}; font-weight: 600; margin-left: 6px;">({status})</span></div><div class="tf-ats-detail">{detail}</div></div><div class="tf-ats-score" style="color: {score_color};">{score}%</div></div>"""
        rows_html += row_block
        
    html = f"""<div class="tf-card"><div class="tf-card-header"><div><div class="tf-card-title">ATS Compatibility Analysis</div><div class="tf-card-subtitle">Applicant Tracking System parse readiness score</div></div></div><div>{rows_html}</div></div>"""
    st.markdown(html, unsafe_allow_html=True)


def render_priority_badge(priority: str) -> str:
    """Return HTML string for skill learning priority badge."""
    p_upper = priority.upper()
    if p_upper == SkillPriority.HIGH:
        return '<span class="tf-priority-pill tf-priority-high">High Priority</span>'
    elif p_upper == SkillPriority.MEDIUM:
        return '<span class="tf-priority-pill tf-priority-medium">Medium Priority</span>'
    return '<span class="tf-priority-pill tf-priority-low">Low Priority</span>'


def render_status_badge(status: str) -> str:
    """Return HTML string for candidate status pill with proper semantic theme variables."""
    st_str = str(status)
    if st_str in ["Strong Match", "Recommended", CandidateStatus.RECOMMENDED]:
        return f'<span class="tf-status-pill tf-status-recommended">✓ {st_str}</span>'
    elif st_str in ["Good Match", "Review", CandidateStatus.REVIEW]:
        return f'<span class="tf-status-pill tf-status-good">★ {st_str}</span>'
    elif st_str in ["Partial Match"]:
        return f'<span class="tf-status-pill tf-status-review">⚡ {st_str}</span>'
    elif st_str in ["Low Match", CandidateStatus.LOW_MATCH]:
        return f'<span class="tf-status-pill tf-status-low">✕ {st_str}</span>'
    return f'<span class="tf-status-pill tf-status-review">{st_str}</span>'
