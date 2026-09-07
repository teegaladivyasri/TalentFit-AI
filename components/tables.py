"""Candidate tables and comparative matrices."""

import streamlit as st
from typing import List, Dict, Any, Callable
from utils.constants import CandidateStatus
from components.score import get_score_color, render_status_badge
from components.cards import render_skill_badges


def render_candidate_rankings_table(
    candidates: List[Dict[str, Any]], 
    on_view_details: Callable[[str], None],
    on_toggle_compare: Callable[[str], None],
    selected_compare_ids: List[str]
) -> None:
    """Render an interactive recruiter candidate ranking table with actions."""
    if not candidates:
        st.markdown(
            """
            <div class="tf-card" style="text-align: center; padding: 2.5rem 1rem;">
                <div style="font-size: 1.1rem; font-weight: 600; color: var(--text-primary);">No candidates match the filter criteria</div>
                <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">Try adjusting your search query, minimum match score, or status filters.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Table Header
    header_cols = st.columns([0.6, 2.2, 0.9, 1.1, 1.7, 1.7, 1.1, 1.9])
    header_cols[0].markdown("**Rank**")
    header_cols[1].markdown("**Candidate & Resume**")
    header_cols[2].markdown("**Match**")
    header_cols[3].markdown("**Req. Coverage**")
    header_cols[4].markdown("**Matched Required**")
    header_cols[5].markdown("**Missing Required**")
    header_cols[6].markdown("**Status**")
    header_cols[7].markdown("**Actions**")
    
    st.markdown("<hr style='margin: 4px 0 10px 0; border: none; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)

    for cand in candidates:
        cand_id = cand["id"]
        c_cols = st.columns([0.6, 2.2, 0.9, 1.1, 1.7, 1.7, 1.1, 1.9])
        
        # 1. Rank
        c_cols[0].markdown(f"<span style='font-weight: 700; color: var(--text-primary); font-size: 0.95rem;'>#{cand['rank']}</span>", unsafe_allow_html=True)
        
        # 2. Name + filename
        filename_display = cand.get('filename', 'Resume.pdf')
        c_cols[1].markdown(
            f"<div><div style='font-weight:600; color:var(--text-primary); font-size:0.9rem;'>{cand['name']}</div><div style='font-size:0.75rem; color:var(--text-muted); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;' title='{filename_display}'>📄 {filename_display}</div></div>", 
            unsafe_allow_html=True
        )
        
        # 3. Overall Match
        ov_color = get_score_color(cand['overall_match'])
        c_cols[2].markdown(
            f"<span style='font-weight: 800; color: {ov_color}; font-size: 1.05rem;'>{cand['overall_match']}%</span>", 
            unsafe_allow_html=True
        )
        
        # 4. Required Skill Coverage
        req_cov = cand.get('required_skill_coverage', cand.get('jd_coverage', 0))
        req_color = "#10B981" if req_cov >= 75 else ("#F59E0B" if req_cov >= 50 else "#EF4444")
        c_cols[3].markdown(
            f"<span style='font-weight: 600; color: {req_color}; font-size: 0.95rem;'>{req_cov}%</span>", 
            unsafe_allow_html=True
        )
        
        # 5. Matched Required Skills preview
        matched_req = cand.get("matched_required_skills") or cand.get("matched_skills", [])
        with c_cols[4]:
            if matched_req:
                pills = "".join(f"<span class='tf-tag tf-tag-matched' style='font-size:0.7rem; margin:1px 2px;'>{s}</span>" for s in matched_req[:3])
                if len(matched_req) > 3:
                    pills += f"<span style='font-size:0.7rem; color:var(--text-muted);'> +{len(matched_req)-3}</span>"
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.markdown("<span style='font-size:0.75rem; color:var(--text-muted);'>None detected</span>", unsafe_allow_html=True)

        # 6. Missing Required Skills preview
        missing_req = cand.get("missing_required_skills") or cand.get("missing_skills", [])
        with c_cols[5]:
            if missing_req:
                pills = "".join(f"<span class='tf-tag tf-tag-missing' style='font-size:0.7rem; margin:1px 2px;'>{s}</span>" for s in missing_req[:3])
                if len(missing_req) > 3:
                    pills += f"<span style='font-size:0.7rem; color:var(--text-muted);'> +{len(missing_req)-3}</span>"
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.markdown("<span style='font-size:0.75rem; color:#10B981; font-weight:600;'>✓ All met</span>", unsafe_allow_html=True)
        
        # 7. Status Pill
        c_cols[6].markdown(render_status_badge(cand['status']), unsafe_allow_html=True)
        
        # 8. Action Buttons
        with c_cols[7]:
            act_c1, act_c2 = st.columns(2, gap="small")
            with act_c1:
                if st.button("Details", key=f"view_cand_{cand_id}", use_container_width=True):
                    on_view_details(cand_id)
            with act_c2:
                is_compared = cand_id in selected_compare_ids
                btn_label = "✓ Matrix" if is_compared else "+ Compare"
                btn_type = "primary" if is_compared else "secondary"
                if st.button(btn_label, key=f"compare_btn_{cand_id}", type=btn_type, use_container_width=True):
                    on_toggle_compare(cand_id)
                
        st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid var(--border-subtle); opacity: 0.5;'>", unsafe_allow_html=True)


def render_comparison_matrix(candidates: List[Dict[str, Any]]) -> None:
    """Render a side-by-side comparative table for chosen candidates."""
    if not candidates:
        st.info("Select at least 2 candidates from the screening table to compare them side-by-side.")
        return
        
    cols = st.columns([1.8] + [2.2 for _ in candidates])
    
    # Header Row: Names
    cols[0].markdown("**Candidate Profile**")
    for i, c in enumerate(candidates):
        cols[i+1].markdown(f"<div style='font-weight:700; font-size:1.05rem; color:var(--text-primary);'>{c['name']}</div>", unsafe_allow_html=True)
        cols[i+1].markdown(f"<div style='font-size:0.75rem; color:var(--text-muted);'>📄 {c.get('filename', 'Resume.pdf')}</div>", unsafe_allow_html=True)
        
    st.markdown("<hr style='margin: 6px 0 12px 0; border-top: 1px solid var(--border-strong);'>", unsafe_allow_html=True)

    # Core Metrics rows
    rows = [
        ("Overall Match Score", lambda c: f"<strong style='color:{get_score_color(c['overall_match'])}; font-size:1.15rem;'>{c['overall_match']}%</strong>"),
        ("Required Skill Coverage", lambda c: f"<strong>{c.get('required_skill_coverage', c.get('jd_coverage', 0))}%</strong>"),
        ("Skill Match Score", lambda c: f"<span>{c.get('skill_match', 0)}%</span>"),
        ("Content Similarity", lambda c: f"<span>{c.get('content_similarity', 0)}%</span>"),
        ("ATS Parse Readiness", lambda c: f"<span>{c.get('ats_score', 'N/A')}%</span>" if c.get('ats_score') is not None else "<span style='color:var(--text-muted);'>N/A</span>"),
        ("Screening Status", lambda c: render_status_badge(c['status'])),
    ]
    
    for row_title, getter in rows:
        r_cols = st.columns([1.8] + [2.2 for _ in candidates])
        r_cols[0].markdown(f"**{row_title}**")
        for i, c in enumerate(candidates):
            r_cols[i+1].markdown(getter(c), unsafe_allow_html=True)
        st.markdown("<hr style='margin: 6px 0; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)

    # Matched Required Skills row
    r_cols = st.columns([1.8] + [2.2 for _ in candidates])
    r_cols[0].markdown("**Matched Required Skills**")
    for i, c in enumerate(candidates):
        with r_cols[i+1]:
            matched_req = c.get("matched_required_skills") or c.get("matched_skills", [])
            render_skill_badges(matched_req, "matched")
            
    st.markdown("<hr style='margin: 6px 0; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)

    # Missing Required Skills row
    r_cols = st.columns([1.8] + [2.2 for _ in candidates])
    r_cols[0].markdown("**Missing Required Skills**")
    for i, c in enumerate(candidates):
        with r_cols[i+1]:
            missing_req = c.get("missing_required_skills") or c.get("missing_skills", [])
            if missing_req:
                render_skill_badges(missing_req, "missing")
            else:
                st.markdown("<span style='font-size:0.8rem; color:#10B981; font-weight:600;'>✓ 100% Required Skills Met</span>", unsafe_allow_html=True)
            
    st.markdown("<hr style='margin: 6px 0; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)

    # Missing Preferred Skills row
    r_cols = st.columns([1.8] + [2.2 for _ in candidates])
    r_cols[0].markdown("**Missing Preferred Skills**")
    for i, c in enumerate(candidates):
        with r_cols[i+1]:
            missing_pref = c.get("missing_preferred_skills", [])
            if missing_pref:
                render_skill_badges(missing_pref, "missing")
            else:
                st.markdown("<span style='font-size:0.8rem; color:var(--text-muted);'>None missing</span>", unsafe_allow_html=True)

    st.markdown("<hr style='margin: 6px 0; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)

    # Additional Resume Skills row
    r_cols = st.columns([1.8] + [2.2 for _ in candidates])
    r_cols[0].markdown("**Additional Resume Skills**")
    for i, c in enumerate(candidates):
        with r_cols[i+1]:
            extra = c.get("extra_skills", [])
            if extra:
                render_skill_badges(extra[:6], "neutral")
                if len(extra) > 6:
                    st.caption(f"+{len(extra)-6} more skills")
            else:
                st.markdown("<span style='font-size:0.8rem; color:var(--text-muted);'>None detected</span>", unsafe_allow_html=True)
