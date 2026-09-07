"""Centralized session state manager for Streamlit application."""

import streamlit as st
from typing import Any, Optional, List, Dict
from utils.constants import Routes, RecruiterMode, ThemeMode


DEFAULT_STATE = {
    "current_page": Routes.HOME,
    "theme": ThemeMode.LIGHT,
    
    # Job Seeker State
    "js_resume_file": None,
    "js_resume_name": None,
    "js_resume_text": "",
    "js_resume_processed": None,
    "js_resume_skills": None,
    "js_jd_mode": "paste",
    "js_jd_text": "",
    "js_jd_file": None,
    "js_jd_extracted_text": "",
    "js_jd_processed": None,
    "js_jd_skills": None,
    "js_match_result": None,
    "js_ats_result": None,
    "js_recommendations": None,
    "js_learning_roadmap": None,
    "js_guidance_summary": None,
    "js_analysis_results": None,
    
    # Recruiter State
    "rec_jd_mode": "paste",
    "rec_jd_text": "",
    "rec_jd_file": None,
    "rec_jd_extracted_text": "",
    "rec_jd_processed": None,
    "rec_jd_skills": None,
    "rec_screening_mode": RecruiterMode.BATCH,
    "rec_single_resume": None,
    "rec_single_resume_name": None,
    "rec_single_resume_text": "",
    "rec_single_resume_processed": None,
    "rec_single_resume_skills": None,
    "rec_single_match_result": None,
    "rec_batch_resumes": [],
    "rec_batch_extracted_candidates": [],
    "rec_screening_results": None,
    "rec_selected_candidate_id": "cand-01",
    "rec_compared_candidate_ids": ["cand-01", "cand-02"],
}


def init_session_state(state: Optional[Any] = None) -> None:
    """Initialize all default session state variables if not already set."""
    target = st.session_state if state is None else state
    for key, val in DEFAULT_STATE.items():
        if key not in target:
            target[key] = val


def navigate_to(page: str, **kwargs: Any) -> None:
    """Navigate to a specific page route and set any custom state properties."""
    st.session_state.current_page = page
    for k, v in kwargs.items():
        st.session_state[k] = v


def toggle_theme() -> None:
    """Toggle between Light and Dark mode."""
    if st.session_state.get("theme", ThemeMode.LIGHT) == ThemeMode.LIGHT:
        st.session_state["theme"] = ThemeMode.DARK
    else:
        st.session_state["theme"] = ThemeMode.LIGHT


def get_theme() -> str:
    """Get active theme mode ('light' or 'dark')."""
    return st.session_state.get("theme", ThemeMode.LIGHT)


def reset_job_seeker_inputs(state: Optional[Any] = None) -> None:
    """Clear all job seeker inputs, extracted text, skills, analysis results, and widget keys."""
    target = st.session_state if state is None else state
    target["js_resume_file"] = None
    target["js_resume_name"] = None
    target["js_resume_text"] = ""
    target["js_resume_processed"] = None
    target["js_resume_skills"] = None
    target["js_jd_mode"] = "paste"
    target["js_jd_text"] = ""
    target["js_jd_text_input"] = ""
    target["js_jd_file"] = None
    target["js_jd_extracted_text"] = ""
    target["js_jd_processed"] = None
    target["js_jd_skills"] = None
    target["js_match_result"] = None
    target["js_ats_result"] = None
    target["js_recommendations"] = None
    target["js_learning_roadmap"] = None
    target["js_guidance_summary"] = None
    target["js_analysis_results"] = None
    
    # Clear widget keys if present
    for widget_key in ["js_resume_uploader", "js_jd_file_uploader"]:
        if widget_key in target:
            try:
                del target[widget_key]
            except Exception:
                target[widget_key] = None


def reset_recruiter_inputs(state: Optional[Any] = None) -> None:
    """Clear all recruiter inputs, batch screening results, processed/skills state, and widget keys."""
    target = st.session_state if state is None else state
    target["rec_jd_mode"] = "paste"
    target["rec_jd_text"] = ""
    target["rec_jd_text_input"] = ""
    target["rec_jd_file"] = None
    target["rec_jd_extracted_text"] = ""
    target["rec_jd_processed"] = None
    target["rec_jd_skills"] = None
    target["rec_screening_mode"] = RecruiterMode.BATCH
    target["rec_single_resume"] = None
    target["rec_single_resume_name"] = None
    target["rec_single_resume_text"] = ""
    target["rec_single_resume_processed"] = None
    target["rec_single_resume_skills"] = None
    target["rec_single_match_result"] = None
    target["rec_batch_resumes"] = []
    target["rec_batch_extracted_candidates"] = []
    target["rec_screening_results"] = None
    target["rec_selected_candidate_id"] = "cand-01"
    target["rec_compared_candidate_ids"] = ["cand-01", "cand-02"]
    
    # Clear widget keys if present
    for widget_key in [
        "rec_jd_file_input", 
        "rec_single_resume_uploader", 
        "rec_batch_resumes_uploader", 
        "rec_filter_search",
        "rec_filter_score_range",
        "rec_filter_req_cov",
        "rec_filter_status",
        "rec_filter_skill",
        "rec_filter_sort",
        "comp_multiselect"
    ]:
        if widget_key in target:
            try:
                del target[widget_key]
            except Exception:
                target[widget_key] = None
