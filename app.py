"""TalentFit AI - Main Application Entrypoint.

AI Resume Screening & Career Matching Platform (Phase 1).
"""

import streamlit as st
from utils.constants import APP_TITLE, APP_SUBTITLE, Routes
from utils.session_state import init_session_state
from components.theme import apply_theme
from components.navbar import render_navbar

# Import Page Views
from pages.home import render_home_page
from pages.job_seeker import render_job_seeker_page
from pages.candidate_analysis import render_candidate_analysis_page
from pages.recruiter import render_recruiter_page
from pages.recruiter_screening import render_recruiter_screening_page
from pages.candidate_details import render_candidate_details_page
from pages.comparison import render_comparison_page


def configure_page() -> None:
    """Set global Streamlit page configurations."""
    st.set_page_config(
        page_title=f"{APP_TITLE} — {APP_SUBTITLE}",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="collapsed"
    )


def render_footer() -> None:
    """Render subtle, clean SaaS product footer."""
    st.markdown(
        """
        <div style="margin-top: 4rem; padding-top: 1.5rem; border-top: 1px solid var(--border-subtle); display: flex; align-items: center; justify-content: space-between; font-size: 0.78rem; color: var(--text-muted);">
            <div>
                <strong>TalentFit AI</strong> — Intelligent Career Matching & Candidate Screening Platform
            </div>
            <div>
                College Project Architecture • Phase 1 Deliverable
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def main() -> None:
    """Main routing and execution controller."""
    # 1. Configure Streamlit page
    configure_page()
    
    # 2. Initialize Session State
    init_session_state()
    
    # 3. Apply Theme & Design Tokens
    apply_theme()
    
    # 4. Render Global Top Navigation
    render_navbar()
    
    # 5. Route to Active Page
    current_page = st.session_state.get("current_page", Routes.HOME)
    
    if current_page == Routes.HOME:
        render_home_page()
    elif current_page == Routes.JOB_SEEKER:
        render_job_seeker_page()
    elif current_page == Routes.JOB_SEEKER_RESULTS:
        render_candidate_analysis_page()
    elif current_page == Routes.RECRUITER:
        render_recruiter_page()
    elif current_page == Routes.RECRUITER_SCREENING:
        render_recruiter_screening_page()
    elif current_page == Routes.CANDIDATE_DETAILS:
        render_candidate_details_page()
    elif current_page == Routes.CANDIDATE_COMPARISON:
        render_comparison_page()
    else:
        render_home_page()
        
    # 6. Render Footer
    render_footer()


if __name__ == "__main__":
    main()
