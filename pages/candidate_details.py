"""Recruiter Candidate Details & Deep Evaluation Report."""

import textwrap
import streamlit as st
from utils.constants import Routes
from utils.session_state import navigate_to
from data.mock_data import get_candidate_by_id
from components.score import (
    render_overall_match_banner, 
    render_status_badge, 
    get_score_color
)
from components.cards import render_metric_card, render_skill_badges


def render_candidate_details_page() -> None:
    """Render the comprehensive candidate evaluation report for recruiters."""
    cand_id = st.session_state.get("rec_selected_candidate_id", "cand-01")
    
    # 1. Search in active session screening results first
    candidate = None
    active_screenings = st.session_state.get("rec_screening_results")
    if active_screenings:
        for c in active_screenings:
            if c.get("id") == cand_id:
                candidate = c
                break
                
    # 2. Fallback to mock data lookup if not found
    if not candidate:
        candidate = get_candidate_by_id(cand_id)
    
    if not candidate:
        st.error("Candidate record not found.")
        if st.button("Return to Screening", key="btn_not_found_back"):
            navigate_to(Routes.RECRUITER_SCREENING)
            st.rerun()
        return

    # Top Navigation Row
    n_col1, n_col2, n_col3 = st.columns([1.5, 3.0, 1.8])
    with n_col1:
        if st.button("← Back to Rankings", key="btn_back_to_rankings", type="secondary"):
            navigate_to(Routes.RECRUITER_SCREENING)
            st.rerun()
            
    with n_col3:
        compared_ids = st.session_state.get("rec_compared_candidate_ids", [])
        is_in_matrix = cand_id in compared_ids
        matrix_label = "✓ In Comparison Matrix" if is_in_matrix else "+ Add to Comparison"
        if st.button(matrix_label, key="btn_detail_toggle_compare", type="primary" if is_in_matrix else "secondary", use_container_width=True):
            if is_in_matrix:
                compared_ids.remove(cand_id)
            else:
                if len(compared_ids) >= 4:
                    st.warning("Maximum of 4 candidates can be compared concurrently.")
                else:
                    compared_ids.append(cand_id)
            st.session_state["rec_compared_candidate_ids"] = compared_ids
            st.rerun()

    # Candidate Header Banner
    render_overall_match_banner(
        score=candidate["overall_match"],
        role_title=f"{candidate['name']} — Candidate Evaluation",
        candidate_name=f"Document: {candidate.get('filename', 'Resume.pdf')}"
    )
    
    # 4 Core KPI Metrics
    req_cov = candidate.get('required_skill_coverage', candidate.get('jd_coverage', 0))
    ats_score = candidate.get('ats_score', 80)
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Skill Match", f"{candidate['skill_match']}%", "Direct requirement overlap (70% wt)", "#10B981")
    with m2:
        render_metric_card("Content Similarity", f"{candidate.get('content_similarity', 0)}%", "Text semantics (30% wt)", "#2563EB")
    with m3:
        render_metric_card("Required Skill Coverage", f"{req_cov}%", "Mandatory qualifications met", "#3B82F6")
    with m4:
        render_metric_card("ATS Parse Readiness", f"{ats_score}%", "Structural parse indicator", "#8B5CF6")

    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)

    # 70/30 Explainable Scoring Formula Card
    st.markdown(
        textwrap.dedent(f"""
        <div class="tf-card" style="margin-bottom: 1.25rem;">
            <div class="tf-card-header">
                <div class="tf-card-title">Score Calculation & Weighting Breakdown</div>
                <div>{render_status_badge(candidate['status'])}</div>
            </div>
            <div style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6; margin-bottom: 0.75rem;">
                The overall compatibility score is calculated using the project's transparent mathematical model:
            </div>
            <div style="background-color: var(--bg-surface-alt); padding: 12px 16px; border-radius: 6px; border: 1px solid var(--border-subtle); font-family: monospace; font-size: 0.85rem; color: var(--text-primary); margin-bottom: 0.75rem;">
                Overall Score ({candidate['overall_match']}%) = 0.70 × Skill Match ({candidate['skill_match']}%) + 0.30 × Content Similarity ({candidate.get('content_similarity', 0)}%)
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted);">
                • <strong>Skill Match (70%):</strong> Ratio of matched JD skill weights to total JD skill weights (Required: 1.0, Preferred: 0.5).<br>
                • <strong>Content Similarity (30%):</strong> Cosine similarity between resume and job description text via TF-IDF vectorization.
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

    # Matched vs Missing Skills (Required & Preferred)
    matched_req = candidate.get("matched_required_skills") or candidate.get("matched_skills", [])
    missing_req = candidate.get("missing_required_skills") or [s for s in candidate.get("missing_skills", []) if s in candidate.get("required_skills", [])]
    missing_pref = candidate.get("missing_preferred_skills", [])
    extra_skills = candidate.get("extra_skills", [])

    s_col1, s_col2 = st.columns(2, gap="medium")
    
    with s_col1:
        st.markdown(
            textwrap.dedent(f"""
            <div class="tf-card" style="height: 100%;">
                <div class="tf-card-header">
                    <div class="tf-card-title" style="color: var(--tag-good-text);">✓ Satisfied Required Skills</div>
                    <span class="tf-tag tf-tag-matched">{len(matched_req)} Verified</span>
                </div>
            """),
            unsafe_allow_html=True
        )
        if matched_req:
            render_skill_badges(matched_req, "matched")
        else:
            st.markdown("<span style='font-size:0.85rem; color:var(--text-muted);'>No required skills detected.</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with s_col2:
        st.markdown(
            textwrap.dedent(f"""
            <div class="tf-card" style="height: 100%;">
                <div class="tf-card-header">
                    <div class="tf-card-title" style="color: var(--tag-bad-text);">✕ Missing Required Skills</div>
                    <span class="tf-tag tf-tag-missing">{len(missing_req)} Gaps</span>
                </div>
            """),
            unsafe_allow_html=True
        )
        if missing_req:
            render_skill_badges(missing_req, "missing")
        else:
            st.markdown("<div style='font-size:0.85rem; color:#10B981; font-weight:600; padding:4px 0;'>✓ 100% of core role requirements detected in resume.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)

    # Missing Preferred & Extra Skills
    p_col1, p_col2 = st.columns(2, gap="medium")
    
    with p_col1:
        if missing_pref:
            st.markdown(
                textwrap.dedent(f"""
                <div class="tf-card" style="height: 100%;">
                    <div class="tf-card-header">
                        <div class="tf-card-title" style="color: var(--tag-warn-text);">⚡ Missing Preferred Qualifications</div>
                        <span class="tf-tag tf-tag-warn">{len(missing_pref)} Nice-to-Have</span>
                    </div>
                """),
                unsafe_allow_html=True
            )
            render_skill_badges(missing_pref, "missing")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                textwrap.dedent("""
                <div class="tf-card" style="height: 100%;">
                    <div class="tf-card-header">
                        <div class="tf-card-title">⚡ Preferred Qualifications</div>
                    </div>
                    <div style="font-size:0.85rem; color:var(--text-muted);">No preferred qualification gaps identified.</div>
                </div>
                """),
                unsafe_allow_html=True
            )

    with p_col2:
        if extra_skills:
            st.markdown(
                textwrap.dedent(f"""
                <div class="tf-card" style="height: 100%;">
                    <div class="tf-card-header">
                        <div class="tf-card-title">+ Additional Detected Skills</div>
                        <span class="tf-tag tf-tag-neutral">{len(extra_skills)} Detected</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                        Competencies on resume outside specific job description scope:
                    </div>
                """),
                unsafe_allow_html=True
            )
            render_skill_badges(extra_skills[:8], "neutral")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                textwrap.dedent("""
                <div class="tf-card" style="height: 100%;">
                    <div class="tf-card-header">
                        <div class="tf-card-title">+ Additional Detected Skills</div>
                    </div>
                    <div style="font-size:0.85rem; color:var(--text-muted);">No additional peripheral skills detected.</div>
                </div>
                """),
                unsafe_allow_html=True
            )

    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)

    # ATS Parse-Readiness Breakdown (Kept on recruiter side)
    ats_breakdown = candidate.get("ats_breakdown")
    if ats_breakdown:
        st.markdown(
            textwrap.dedent(f"""
            <div class="tf-card" style="margin-bottom: 1.25rem;">
                <div class="tf-card-header">
                    <div class="tf-card-title">ATS Parse-Readiness Indicators ({candidate.get('ats_score', 80)}/100)</div>
                    <span class="tf-tag tf-tag-neutral">Structure & Format</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 8px;">
                    <div style="background-color: var(--bg-surface-alt); padding: 10px; border-radius: 6px; border: 1px solid var(--border-subtle);">
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Extractability</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">{ats_breakdown.get('text_extractability', 100)}%</div>
                    </div>
                    <div style="background-color: var(--bg-surface-alt); padding: 10px; border-radius: 6px; border: 1px solid var(--border-subtle);">
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Section Structure</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">{ats_breakdown.get('section_structure', 85)}%</div>
                    </div>
                    <div style="background-color: var(--bg-surface-alt); padding: 10px; border-radius: 6px; border: 1px solid var(--border-subtle);">
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Contact Details</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">{ats_breakdown.get('contact_information', 100)}%</div>
                    </div>
                    <div style="background-color: var(--bg-surface-alt); padding: 10px; border-radius: 6px; border: 1px solid var(--border-subtle);">
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Skill Visibility</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">{ats_breakdown.get('skill_visibility', 80)}%</div>
                    </div>
                    <div style="background-color: var(--bg-surface-alt); padding: 10px; border-radius: 6px; border: 1px solid var(--border-subtle);">
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Organization</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">{ats_breakdown.get('content_organization', 85)}%</div>
                    </div>
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )

    # Decision Support Advisory Box
    st.markdown(
        textwrap.dedent(f"""
        <div class="tf-card" style="border-left: 4px solid var(--primary);">
            <div class="tf-card-header">
                <div class="tf-card-title">Recruiter Decision Support Assessment</div>
                <span class="tf-nav-badge">Advisory</span>
            </div>
            <div style="font-size: 0.9rem; color: var(--text-primary); font-weight: 500; line-height: 1.5; margin-bottom: 6px;">
                {candidate.get('recommendation_note', 'Candidate evaluated against job description requirements.')}
            </div>
            <div style="font-size: 0.78rem; color: var(--text-muted); font-style: italic;">
                Note: Automated match compatibility scores and skill gap analyses provide screening aids. Final candidate shortlisting, interview invitations, and hiring decisions remain the sole responsibility of the hiring team.
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )
