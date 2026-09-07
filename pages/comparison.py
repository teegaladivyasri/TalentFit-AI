"""Candidate Comparison Matrix View."""

import textwrap
import streamlit as st
from utils.constants import Routes
from utils.session_state import navigate_to
from components.tables import render_comparison_matrix


def render_comparison_page() -> None:
    """Render the Candidate Comparison Side-by-Side Matrix."""
    all_candidates = st.session_state.get("rec_screening_results") or []
    compared_ids = st.session_state.get("rec_compared_candidate_ids", [])
    
    # Header & Back Row
    nav_col1, nav_col2 = st.columns([1.5, 4.5])
    with nav_col1:
        if st.button("← Back to Rankings", key="btn_back_from_compare", type="secondary"):
            navigate_to(Routes.RECRUITER_SCREENING)
            st.rerun()

    st.markdown(
        textwrap.dedent("""
        <div style="margin-bottom: 1.25rem;">
            <div style="font-size: 1.75rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.02em;">Candidate Comparison Matrix</div>
            <div style="font-size: 0.95rem; color: var(--text-secondary); margin-top: 4px;">
                Direct side-by-side benchmarking of key competencies, scores, and missing requirements across selected candidates.
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

    if not all_candidates:
        st.info("No candidates available for comparison. Please run screening from the Recruiter Hub first.")
        if st.button("Go to Recruiter Hub", key="btn_go_to_hub_from_empty_comp"):
            navigate_to(Routes.RECRUITER)
            st.rerun()
        return
    
    # Candidate Selector multiselect
    candidate_options = {c["id"]: f"{c['name']} ({c['overall_match']}%) — {c.get('filename', '')}" for c in all_candidates}
    
    # Ensure default IDs exist in candidate options
    valid_defaults = [cid for cid in compared_ids if cid in candidate_options]
    if not valid_defaults:
        valid_defaults = list(candidate_options.keys())[:2]

    selected_ids = st.multiselect(
        label="Select candidates to benchmark (2 to 4 candidates):",
        options=list(candidate_options.keys()),
        default=valid_defaults,
        format_func=lambda x: candidate_options.get(x, x),
        max_selections=4,
        key="comp_multiselect"
    )
    st.session_state["rec_compared_candidate_ids"] = selected_ids
    
    selected_candidates = [c for c in all_candidates if c["id"] in selected_ids]
    
    if len(selected_candidates) < 2:
        st.markdown(
            textwrap.dedent("""
            <div class="tf-card" style="text-align: center; padding: 2.5rem 1rem; margin-top: 1rem;">
                <div style="font-size: 1.1rem; font-weight: 600; color: var(--text-primary);">Select at least 2 candidates to compare</div>
                <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">
                    Choose between 2 and 4 candidate profiles from the dropdown above to view the side-by-side benchmarking matrix.
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )
        return
        
    st.markdown(
        """<div class="tf-card" style="margin-top: 1rem;">""",
        unsafe_allow_html=True
    )
    
    render_comparison_matrix(selected_candidates)
    
    st.markdown("</div>", unsafe_allow_html=True)
