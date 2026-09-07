"""Home / Landing Page for TalentFit AI."""

import streamlit as st
from utils.constants import Routes
from utils.session_state import navigate_to
from components.cards import render_hero_preview_mockup


def render_home_page() -> None:
    """Render the modern SaaS landing page with hero, value propositions, 3-step workflow, and platform highlights."""
    
    # 1. Hero Section
    st.markdown('<div class="tf-hero">', unsafe_allow_html=True)
    
    hero_col1, hero_col2 = st.columns([1.2, 1.0], gap="large")
    
    with hero_col1:
        st.markdown(
            """
            <span class="tf-hero-badge">AI-Powered Career & Hiring Intelligence</span>
            <div class="tf-hero-title">Know how well your resume matches the job.</div>
            <div class="tf-hero-desc">
                TalentFit AI helps job seekers understand their resume-to-job fit and identify actionable improvements, while enabling recruiters to screen and rank candidate pools objectively.
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        btn_c1, btn_c2, _ = st.columns([1.3, 1.2, 0.5])
        with btn_c1:
            if st.button("Analyze Your Resume", key="hero_cta_js", type="primary", use_container_width=True):
                navigate_to(Routes.JOB_SEEKER)
                st.rerun()
        with btn_c2:
            if st.button("Screen Candidates", key="hero_cta_rec", type="secondary", use_container_width=True):
                navigate_to(Routes.RECRUITER)
                st.rerun()
                
    with hero_col2:
        render_hero_preview_mockup()
        
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 2.25rem 0 1.75rem 0; border: none; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)
    
    # 2. How It Works (3-Step Section)
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1.75rem;">
            <div style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em;">HOW IT WORKS</div>
            <div style="font-size: 1.6rem; font-weight: 700; color: var(--text-primary); margin-top: 4px; letter-spacing: -0.02em;">Three systematic steps from document to decision</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    step_cols = st.columns(3, gap="medium")
    
    steps = [
        ("01", "Upload", "Upload your resume and provide the target job description via text or document upload."),
        ("02", "Analyze", "TalentFit AI extracts technical competencies across 93 canonical skills and compares the candidate against role requirements."),
        ("03", "Improve / Screen", "Candidates receive actionable improvement guidance, while recruiters receive structured candidate screening and ranking results.")
    ]
    
    for i, (num, title, desc) in enumerate(steps):
        with step_cols[i]:
            st.markdown(
                f"""
                <div class="tf-card" style="height: 100%; display: flex; flex-direction: column;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span class="tf-step-badge">{num}</span>
                        <span style="font-weight: 700; font-size: 1rem; color: var(--text-primary);">{title}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; flex-grow: 1;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    st.markdown("<hr style='margin: 2.25rem 0 1.75rem 0; border: none; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)
    
    # 3. Dual Value Proposition Section (Job Seekers & Recruiters)
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1.75rem;">
            <div style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em;">PLATFORM WORKFLOWS</div>
            <div style="font-size: 1.6rem; font-weight: 700; color: var(--text-primary); margin-top: 4px; letter-spacing: -0.02em;">Tailored capabilities for candidates & recruitment teams</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    persona_col1, persona_col2 = st.columns(2, gap="medium")
    
    with persona_col1:
        st.markdown(
            """
            <div class="tf-persona-card">
                <div>
                    <span class="tf-hero-badge" style="font-size: 0.7rem; margin-bottom: 8px;">FOR JOB SEEKERS</span>
                    <div class="tf-persona-title">Improve your resume with evidence, not guesswork.</div>
                    <div class="tf-persona-desc">
                        Upload your resume and a target job description to discover where you stand and what to improve before applying.
                    </div>
                    <ul class="tf-feature-list">
                        <li class="tf-feature-item"><span class="tf-check-bullet">✓</span> Discover your exact JD Match %</li>
                        <li class="tf-feature-item"><span class="tf-check-bullet">✓</span> View skills already present on your resume</li>
                        <li class="tf-feature-item"><span class="tf-check-bullet">✓</span> Identify missing skills from the job description</li>
                        <li class="tf-feature-item"><span class="tf-check-bullet">✓</span> Receive section-by-section resume improvement guidance</li>
                        <li class="tf-feature-item"><span class="tf-check-bullet">✓</span> Explore practical skills worth learning with practice projects</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Analyze My Resume", key="persona_cta_js", type="primary", use_container_width=True):
            navigate_to(Routes.JOB_SEEKER)
            st.rerun()

    with persona_col2:
        st.markdown(
            """
            <div class="tf-persona-card">
                <div>
                    <span class="tf-hero-badge" style="font-size: 0.7rem; margin-bottom: 8px; background-color: var(--tag-neutral-bg); color: var(--text-primary);">FOR RECRUITERS</span>
                    <div class="tf-persona-title">Screen candidates faster and more consistently.</div>
                    <div class="tf-persona-desc">
                        Standardize candidate evaluation with objective skill matching, candidate ranking, and side-by-side matrices.
                    </div>
                    <ul class="tf-feature-list">
                        <li class="tf-feature-item"><span class="tf-check-bullet">✓</span> Upload or provide target Job Description</li>
                        <li class="tf-feature-item"><span class="tf-check-bullet">✓</span> Screen multiple candidate resumes in batch</li>
                        <li class="tf-feature-item"><span class="tf-check-bullet">✓</span> Rank candidates deterministically</li>
                        <li class="tf-feature-item"><span class="tf-check-bullet">✓</span> Search and filter candidate pools effortlessly</li>
                        <li class="tf-feature-item"><span class="tf-check-bullet">✓</span> Inspect candidate details and compare side-by-side</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Start Screening", key="persona_cta_rec", type="secondary", use_container_width=True):
            navigate_to(Routes.RECRUITER)
            st.rerun()

    st.markdown("<hr style='margin: 2.25rem 0 1.75rem 0; border: none; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)

    # 4. Trust & Highlights Strip
    st.markdown(
        """
        <div class="tf-highlights-strip">
            <div class="tf-highlight-item">
                <div class="tf-highlight-title">⚡ Fast In-Memory Processing</div>
                <div class="tf-highlight-desc">Rapid NLP extraction and matching</div>
            </div>
            <div class="tf-highlight-item">
                <div class="tf-highlight-title">🎯 Transparent Matching</div>
                <div class="tf-highlight-desc">Direct skill overlap and requirements coverage</div>
            </div>
            <div class="tf-highlight-item">
                <div class="tf-highlight-title">🔒 Privacy-Preserving</div>
                <div class="tf-highlight-desc">Zero external API calls or data retention</div>
            </div>
            <div class="tf-highlight-item">
                <div class="tf-highlight-title">📚 93 Canonical Skills</div>
                <div class="tf-highlight-desc">Section & alias-aware technical taxonomy</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
