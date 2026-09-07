"""Top navigation bar component for TalentFit AI."""

import streamlit as st
from utils.constants import Routes, APP_TITLE, ThemeMode
from utils.session_state import navigate_to, toggle_theme, get_theme


def render_navbar() -> None:
    """Render the clean SaaS navigation bar."""
    current_page = st.session_state.get("current_page", Routes.HOME)
    current_theme = get_theme()
    
    # Map active page to broad section
    is_home = current_page == Routes.HOME
    is_js = current_page in [Routes.JOB_SEEKER, Routes.JOB_SEEKER_RESULTS]
    is_rec = current_page in [
        Routes.RECRUITER, 
        Routes.RECRUITER_SCREENING, 
        Routes.CANDIDATE_DETAILS, 
        Routes.CANDIDATE_COMPARISON
    ]
    
    # Top navbar layout columns
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([3.2, 1.1, 1.3, 1.3, 1.1])
    
    with nav_col1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 10px; height: 38px;">
                <div style="background-color: var(--primary); color: #ffffff; width: 30px; height: 30px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.9rem; box-shadow: 0 1px 3px rgba(37,99,235,0.25);">TF</div>
                <div style="font-weight: 700; font-size: 1.1rem; letter-spacing: -0.02em; color: var(--text-primary);">{APP_TITLE}</div>
                <span class="tf-nav-badge">Platform</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with nav_col2:
        if st.button("Home", key="nav_home", type="primary" if is_home else "secondary", use_container_width=True):
            navigate_to(Routes.HOME)
            st.rerun()
            
    with nav_col3:
        if st.button("Job Seeker", key="nav_js", type="primary" if is_js else "secondary", use_container_width=True):
            navigate_to(Routes.JOB_SEEKER)
            st.rerun()
            
    with nav_col4:
        if st.button("Recruiter", key="nav_rec", type="primary" if is_rec else "secondary", use_container_width=True):
            navigate_to(Routes.RECRUITER)
            st.rerun()
            
    with nav_col5:
        theme_icon = "🌙 Dark" if current_theme == ThemeMode.LIGHT else "☀️ Light"
        if st.button(theme_icon, key="nav_theme_toggle", use_container_width=True):
            toggle_theme()
            st.rerun()

    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)
