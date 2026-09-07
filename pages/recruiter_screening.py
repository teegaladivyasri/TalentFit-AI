"""Recruiter Batch Candidate Screening & Ranking Page."""

import streamlit as st
from typing import List, Dict, Any
from utils.constants import Routes
from utils.session_state import navigate_to
from components.cards import render_metric_card
from components.tables import render_candidate_rankings_table


def _on_clear_rec_filters() -> None:
    """Safely clear candidate filters before widget rendering."""
    st.session_state["rec_filter_search"] = ""
    st.session_state["rec_filter_score_range"] = "All Scores"
    st.session_state["rec_filter_req_cov"] = "All Coverage"
    st.session_state["rec_filter_status"] = "All Statuses"
    st.session_state["rec_filter_skill"] = "All Skills"
    st.session_state["rec_filter_sort"] = "Overall Match (High to Low)"


def render_recruiter_screening_page() -> None:
    """Render the Recruiter Batch Screening and Candidate Ranking Dashboard."""
    all_candidates = st.session_state.get("rec_screening_results") or []
    compared_ids = st.session_state.get("rec_compared_candidate_ids", [])
    
    # Navigation & Action Row
    nav_col1, nav_col2, nav_col3 = st.columns([1.5, 3.0, 1.8])
    with nav_col1:
        if st.button("← Back to Hub", key="btn_back_to_rec_hub", type="secondary"):
            navigate_to(Routes.RECRUITER)
            st.rerun()
            
    with nav_col3:
        comp_count = len(compared_ids)
        comp_btn_label = f"Compare Selected ({comp_count})"
        if st.button(comp_btn_label, key="btn_go_to_compare", type="primary" if comp_count >= 2 else "secondary", use_container_width=True):
            if comp_count < 2:
                st.warning("Please select at least 2 candidates using the '+ Compare' action in the table below.")
            else:
                navigate_to(Routes.CANDIDATE_COMPARISON)
                st.rerun()

    # Top KPI Metrics
    total_cand = len(all_candidates)
    strong_count = sum(1 for c in all_candidates if c.get("status") in ["Strong Match", "Recommended"])
    good_count = sum(1 for c in all_candidates if c.get("status") in ["Good Match", "Review"])
    avg_match = round(sum(c.get("overall_match", 0) for c in all_candidates) / total_cand, 1) if total_cand > 0 else 0
    avg_req_cov = round(sum(c.get("required_skill_coverage", c.get("jd_coverage", 0)) for c in all_candidates) / total_cand, 1) if total_cand > 0 else 0
    
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        render_metric_card("Screened Candidates", str(total_cand), "Total pool size")
    with m2:
        render_metric_card("Strong Match", str(strong_count), "High fit & coverage", "#10B981")
    with m3:
        render_metric_card("Good Match", str(good_count), "Moderate to solid fit", "#3B82F6")
    with m4:
        render_metric_card("Average Match", f"{avg_match}%", "Overall composite fit", "#2563EB")
    with m5:
        render_metric_card("Avg Req. Coverage", f"{avg_req_cov}%", "Mandatory skill score", "#6366F1")

    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)
    
    # Filter Toolbar Card
    st.markdown(
        """<div class="tf-card" style="padding: 1rem 1.25rem 0.5rem 1.25rem; margin-bottom: 1.25rem;">""",
        unsafe_allow_html=True
    )
    
    tb_head_col1, tb_head_col2 = st.columns([4.2, 1.3])
    with tb_head_col1:
        st.markdown(
            """<div style="font-weight: 600; font-size: 0.95rem; color: var(--text-primary); padding-top: 4px;">Filter & Sort Candidates</div>""",
            unsafe_allow_html=True
        )
    with tb_head_col2:
        st.button(
            "✕ Clear Filters", 
            key="btn_clear_rec_filters", 
            type="secondary", 
            use_container_width=True,
            on_click=_on_clear_rec_filters
        )
    
    # Row 1: Search & Score Filters
    f_col1, f_col2, f_col3 = st.columns([2.0, 1.4, 1.4])
    
    with f_col1:
        search_query = st.text_input(
            "Search Candidates", 
            placeholder="Search by candidate name, filename, or skill (e.g. Python, Alex)...", 
            key="rec_filter_search"
        ).strip().lower()
        
    with f_col2:
        score_filter_opts = ["All Scores", "80%+", "60%+", "40%+", "Below 40%"]
        selected_score_range = st.selectbox("Overall Match Score", score_filter_opts, key="rec_filter_score_range")
        
    with f_col3:
        req_cov_filter_opts = ["All Coverage", "80%+", "60%+", "40%+", "Below 40%"]
        selected_req_range = st.selectbox("Required Skill Coverage", req_cov_filter_opts, key="rec_filter_req_cov")

    # Row 2: Status, Specific Skill, and Sort Order
    f_col4, f_col5, f_col6 = st.columns([1.6, 1.6, 1.8])
    
    with f_col4:
        status_options = ["All Statuses", "Strong Match", "Good Match", "Partial Match", "Low Match"]
        selected_status = st.selectbox("Screening Status", status_options, key="rec_filter_status")
        
    with f_col5:
        all_skills_set = set()
        for c in all_candidates:
            all_skills_set.update(c.get("matched_skills", []))
            all_skills_set.update(c.get("extra_skills", []))
        skill_dropdown_opts = ["All Skills"] + sorted(list(all_skills_set))
        selected_skill = st.selectbox("Filter by Detected Skill", skill_dropdown_opts, key="rec_filter_skill")
        
    with f_col6:
        sort_by = st.selectbox(
            "Sort Order", 
            [
                "Overall Match (High to Low)", 
                "Overall Match (Low to High)", 
                "Required Coverage (High to Low)",
                "Skill Match (High to Low)", 
                "Content Similarity (High to Low)",
                "Candidate Name (A to Z)",
                "Candidate Name (Z to A)"
            ], 
            key="rec_filter_sort"
        )
        
    st.markdown("</div>", unsafe_allow_html=True)

    # In-memory instant filtering
    def candidate_matches_filters(c: Dict[str, Any]) -> bool:
        # 1. Search Query (name, filename, or detected skills)
        if search_query:
            name_match = search_query in c.get("name", "").lower()
            file_match = search_query in c.get("filename", "").lower()
            all_c_skills = [s.lower() for s in c.get("matched_skills", []) + c.get("extra_skills", [])]
            skill_match = any(search_query in s for s in all_c_skills)
            if not (name_match or file_match or skill_match):
                return False

        # 2. Overall Score Filter
        ov = c.get("overall_match", 0)
        if selected_score_range == "80%+":
            if ov < 80: return False
        elif selected_score_range == "60%+":
            if ov < 60: return False
        elif selected_score_range == "40%+":
            if ov < 40: return False
        elif selected_score_range == "Below 40%":
            if ov >= 40: return False

        # 3. Required Skill Coverage Filter
        rc = c.get("required_skill_coverage", c.get("jd_coverage", 0))
        if selected_req_range == "80%+":
            if rc < 80: return False
        elif selected_req_range == "60%+":
            if rc < 60: return False
        elif selected_req_range == "40%+":
            if rc < 40: return False
        elif selected_req_range == "Below 40%":
            if rc >= 40: return False

        # 4. Status Filter
        if selected_status != "All Statuses":
            if c.get("status") != selected_status:
                return False

        # 5. Specific Skill Filter
        if selected_skill != "All Skills":
            c_skills = c.get("matched_skills", []) + c.get("extra_skills", [])
            if selected_skill not in c_skills:
                return False

        return True

    filtered_candidates = [c for c in all_candidates if candidate_matches_filters(c)]
    
    # Sorting
    if sort_by == "Overall Match (High to Low)":
        filtered_candidates.sort(key=lambda x: (-x.get("overall_match", 0), x.get("name", "").lower(), x.get("id", "")))
    elif sort_by == "Overall Match (Low to High)":
        filtered_candidates.sort(key=lambda x: (x.get("overall_match", 0), x.get("name", "").lower(), x.get("id", "")))
    elif sort_by == "Required Coverage (High to Low)":
        filtered_candidates.sort(key=lambda x: (-x.get("required_skill_coverage", x.get("jd_coverage", 0)), -x.get("overall_match", 0), x.get("name", "").lower()))
    elif sort_by == "Skill Match (High to Low)":
        filtered_candidates.sort(key=lambda x: (-x.get("skill_match", 0), -x.get("overall_match", 0), x.get("name", "").lower()))
    elif sort_by == "Content Similarity (High to Low)":
        filtered_candidates.sort(key=lambda x: (-x.get("content_similarity", 0), -x.get("overall_match", 0), x.get("name", "").lower()))
    elif sort_by == "Candidate Name (A to Z)":
        filtered_candidates.sort(key=lambda x: (x.get("name", "").lower(), -x.get("overall_match", 0)))
    elif sort_by == "Candidate Name (Z to A)":
        filtered_candidates.sort(key=lambda x: (x.get("name", "").lower()), reverse=True)

    # Re-index visual rank numbers for the filtered view
    for rank_idx, c in enumerate(filtered_candidates, start=1):
        c["rank"] = rank_idx

    # Callback helpers
    def handle_view_details(candidate_id: str) -> None:
        st.session_state["rec_selected_candidate_id"] = candidate_id
        navigate_to(Routes.CANDIDATE_DETAILS)
        st.rerun()

    def handle_toggle_compare(candidate_id: str) -> None:
        c_list = st.session_state.get("rec_compared_candidate_ids", [])
        if candidate_id in c_list:
            c_list.remove(candidate_id)
        else:
            if len(c_list) >= 4:
                st.warning("Maximum of 4 candidates can be compared concurrently.")
            else:
                c_list.append(candidate_id)
        st.session_state["rec_compared_candidate_ids"] = c_list
        st.rerun()

    # Render Table
    st.markdown(
        f"""
        <div class="tf-card">
            <div class="tf-card-header">
                <div>
                    <div class="tf-card-title">Screened Candidate Rankings</div>
                    <div class="tf-card-subtitle">Showing {len(filtered_candidates)} of {total_cand} candidates</div>
                </div>
            </div>
        """,
        unsafe_allow_html=True
    )
    
    render_candidate_rankings_table(
        candidates=filtered_candidates,
        on_view_details=handle_view_details,
        on_toggle_compare=handle_toggle_compare,
        selected_compare_ids=compared_ids
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
