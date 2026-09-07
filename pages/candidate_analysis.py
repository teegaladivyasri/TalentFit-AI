"""Job Seeker Match Analysis Results Page."""

import textwrap
import streamlit as st
from utils.constants import Routes
from utils.session_state import navigate_to
from components.score import render_overall_match_banner, get_score_color
from components.cards import render_metric_card, render_skill_badges


def render_candidate_analysis_page() -> None:
    """Render the Job Seeker detailed evaluation report, resume improvement suggestions, and learning roadmap."""
    results = st.session_state.get("js_analysis_results")
    if not results:
        st.info("Upload your resume to get started.")
        if st.button("← Go to Resume Match Inputs", key="btn_no_results_back", type="primary"):
            navigate_to(Routes.JOB_SEEKER)
            st.rerun()
        return
        
    scores = results.get("scores", {})
    skills = results.get("skills", {"matched": [], "missing": [], "extra": []})
    section_improvements = results.get("section_improvements", {})
    jd_match_pct = results.get("jd_match_percentage")
    total_jd_skills = results.get("total_jd_skills_count", len(skills["matched"]) + len(skills["missing"]))
    resume_filename = results.get("resume_filename", "Uploaded_Resume.pdf")
    
    # Calculate count of resume improvement action points
    total_improvements_count = sum(len(pts) for pts in section_improvements.values()) if section_improvements else len(results.get("resume_improvements", []))
    
    # Back navigation bar
    nav_c1, nav_c2 = st.columns([1.5, 4.5])
    with nav_c1:
        if st.button("← Back to Inputs", key="btn_back_to_js_inputs", type="secondary"):
            navigate_to(Routes.JOB_SEEKER)
            st.rerun()

    # 1. Handle Job Descriptions with Zero Detected Skills
    if total_jd_skills == 0 or jd_match_pct is None:
        st.markdown(
            textwrap.dedent("""
            <div class="tf-card" style="border-left: 4px solid #F59E0B; background-color: var(--bg-surface-alt); padding: 1.5rem; margin-bottom: 1.5rem;">
                <div style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">
                    ⚠️ Unable to Calculate JD Match
                </div>
                <div style="font-size: 0.92rem; color: var(--text-secondary); line-height: 1.6; margin-bottom: 10px;">
                    We couldn't identify recognizable skills in this job description, so a meaningful match percentage cannot be calculated. Add a more detailed job description containing the required skills, tech stack, and responsibilities.
                </div>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
        if st.button("← Return to Inputs and Update Job Description", key="btn_return_empty_jd", type="primary"):
            navigate_to(Routes.JOB_SEEKER)
            st.rerun()
        return

    # 2. Top Match Score Banner
    render_overall_match_banner(
        score=jd_match_pct,
        role_title=f"{jd_match_pct}% JD Match",
        candidate_name=f"Your resume matches {jd_match_pct}% of the skills identified in this job description. (Document: {resume_filename})"
    )
    
    # 3. Candidate-Facing KPI Metrics Row (Equal height, zero ATS or recruiter metrics)
    m_col1, m_col2, m_col3 = st.columns(3, gap="medium")
    with m_col1:
        render_metric_card("Skills Present", f"{len(skills['matched'])}", "Relevant skills detected on resume", "#10B981")
    with m_col2:
        render_metric_card("Missing Skills", f"{len(skills['missing'])}", "Job description skills not found", "#EF4444")
    with m_col3:
        render_metric_card("Resume Improvements", f"{max(total_improvements_count, 1)}", "Actionable resume enhancements", "#2563EB")

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # 4. Dual Skills Column: Skills You Already Have vs Missing Skills
    skill_col1, skill_col2 = st.columns(2, gap="medium")
    
    with skill_col1:
        st.markdown(
            textwrap.dedent(f"""
            <div class="tf-card" style="height: 100%;">
                <div class="tf-card-header">
                    <div class="tf-card-title" style="color: var(--tag-good-text);">Skills You Already Have</div>
                    <span class="tf-tag tf-tag-matched">{len(skills['matched'])} Verified</span>
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
                    Skills detected in both the target job description and your resume:
                </div>
            """).strip(),
            unsafe_allow_html=True
        )
        if skills["matched"]:
            render_skill_badges(skills["matched"], "matched")
        else:
            st.markdown("<span style='font-size: 0.85rem; color: var(--text-muted);'>No overlapping skills detected.</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with skill_col2:
        st.markdown(
            textwrap.dedent(f"""
            <div class="tf-card" style="height: 100%;">
                <div class="tf-card-header">
                    <div class="tf-card-title" style="color: var(--tag-bad-text);">Skills Missing From Your Resume</div>
                    <span class="tf-tag tf-tag-missing">{len(skills['missing'])} Gaps</span>
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
                    Skills detected in the job description that were not detected in your resume:
                </div>
            """).strip(),
            unsafe_allow_html=True
        )
        if skills["missing"]:
            render_skill_badges(skills["missing"], "missing")
        else:
            st.markdown("<div style='font-size:0.85rem; color:#10B981; font-weight:600; padding:4px 0;'>✓ 100% of skills detected in the job description are present on your resume.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # 5. Optional Additional Skills on Resume
    if skills.get("extra"):
        st.markdown(
            textwrap.dedent(f"""
            <div class="tf-card" style="margin-bottom: 1.5rem;">
                <div class="tf-card-header">
                    <div class="tf-card-title" style="color: var(--text-primary);">+ Additional Candidate Skills</div>
                    <span class="tf-tag tf-tag-neutral">{len(skills['extra'])} Detected</span>
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">
                    Skills detected on your resume beyond the target role's specific requirements:
                </div>
            """).strip(),
            unsafe_allow_html=True
        )
        render_skill_badges(skills["extra"], "neutral")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 6. Dedicated Section: Resume Changes That Can Improve Your Match
    st.markdown(
        textwrap.dedent("""
        <div class="tf-card" style="margin-bottom: 1.5rem;">
            <div class="tf-card-header">
                <div>
                    <div class="tf-card-title">Resume Changes That Can Improve Your Match</div>
                    <div class="tf-card-subtitle">These suggestions are based on skills and information already supported by your resume. Never add a skill you do not genuinely have.</div>
                </div>
            </div>
        """).strip(),
        unsafe_allow_html=True
    )

    # Render section recommendations across 4 clean areas: Summary, Technical Skills, Work Experience, Projects
    sections_map = {
        "Summary": section_improvements.get("Professional Summary", []),
        "Technical Skills": section_improvements.get("Technical Skills", []),
        "Work Experience": section_improvements.get("Work Experience", []),
        "Projects": section_improvements.get("Projects", []),
    }
    
    has_section_content = False
    
    for sec_name, sec_points in sections_map.items():
        if sec_points:
            has_section_content = True
            points_html = "".join([
                f"<div style='display: flex; align-items: flex-start; gap: 8px; margin-bottom: 8px;'><span style='color: #2563EB; font-weight: bold;'>•</span><span style='font-size: 0.875rem; color: var(--text-secondary); line-height: 1.5;'>{pt}</span></div>"
                for pt in sec_points
            ])
            st.markdown(
                textwrap.dedent(f"""
                <div style="background-color: var(--bg-surface-alt); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 12px 14px; margin-bottom: 10px;">
                    <div style="font-weight: 600; font-size: 0.9rem; color: var(--text-primary); margin-bottom: 6px;">📂 {sec_name}</div>
                    {points_html}
                </div>
                """).strip(),
                unsafe_allow_html=True
            )

    # Fallback if section_improvements is empty
    if not has_section_content:
        for imp in results.get("resume_improvements", []):
            st.markdown(
                f"<div style='display: flex; align-items: flex-start; gap: 8px; margin-bottom: 8px;'><span style='color: #2563EB; font-weight: bold;'>•</span><span style='font-size: 0.875rem; color: var(--text-secondary); line-height: 1.5;'>{imp}</span></div>",
                unsafe_allow_html=True
            )

    # Anti-fabrication reminder notice
    st.markdown(
        textwrap.dedent("""
        <div style="font-size: 0.78rem; color: var(--text-muted); font-style: italic; border-top: 1px solid var(--border-subtle); padding-top: 10px; margin-top: 6px;">
            ⚠️ <strong>Integrity Note:</strong> Only add skills or responsibilities that you have genuinely worked with. If you lack experience with a missing skill, treat it as a learning goal in the roadmap below rather than claiming experience.
        </div>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )
    
    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # 7. Dedicated Section: Skills to Learn (Practical Guidance, No Priority Badges)
    skills_to_learn = results.get("skills_to_learn", [])
    if skills_to_learn:
        st.markdown(
            textwrap.dedent("""
            <div class="tf-card">
                <div class="tf-card-header">
                    <div>
                        <div class="tf-card-title">Skills to Learn</div>
                        <div class="tf-card-subtitle">Practical learning sequence, topics, exact search terms, and project ideas for missing job description skills</div>
                    </div>
                </div>
            """).strip(),
            unsafe_allow_html=True
        )
        
        for item in skills_to_learn:
            skill_name = item.get("skill", "")
            category = item.get("category", "Technical")
            what_to_learn = item.get("what_to_learn", item.get("recommended_focus", []))
            learning_seq = item.get("learning_sequence", [
                f"1. Understand core concepts, syntax, and architecture of {skill_name}.",
                f"2. Follow official tutorials to set up a local development environment.",
                f"3. Build a standalone proof-of-concept module exercising key operations.",
                f"4. Integrate {skill_name} with your backend or data workflows.",
                f"5. Add automated unit tests and deploy a working demonstration."
            ])
            practice_project = item.get("practice_project", f"Construct a portfolio project incorporating {skill_name} with test coverage.")
            search_phrases = item.get("search_phrases", [f'"{skill_name} official tutorial"', f'"{skill_name} beginner guide"'])
            resource_types = item.get("resource_types", [f"Official {skill_name} Documentation & Guides", f"freeCodeCamp / Official Developer Portals for {skill_name}"])

            topics_html = "".join([
                f"""<div style="display: inline-flex; align-items: center; background-color: var(--bg-surface-alt); border: 1px solid var(--border-subtle); padding: 4px 8px; border-radius: 4px; font-size: 0.78rem; margin-right: 6px; margin-top: 4px; color: var(--text-secondary);"><span style="color: var(--primary); font-weight: bold; margin-right: 4px;">•</span> {topic}</div>"""
                for topic in what_to_learn
            ])

            seq_html = "".join([
                f"<div style='font-size: 0.82rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: 3px;'>{step}</div>"
                for step in learning_seq
            ])

            search_html = "".join([
                f"""<div style="display: inline-flex; align-items: center; gap: 4px; background-color: var(--bg-surface-alt); border: 1px solid var(--border-subtle); padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; margin-right: 6px; margin-top: 4px; font-family: monospace; color: var(--text-primary);">🔍 {sp}</div>"""
                for sp in search_phrases
            ])

            resources_html = "".join([
                f"""<div style="display: inline-flex; align-items: center; gap: 4px; background-color: var(--bg-surface-alt); border: 1px solid var(--border-subtle); padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; margin-right: 6px; margin-top: 4px; color: var(--text-muted);">📚 {res}</div>"""
                for res in resource_types
            ])
            
            st.markdown(
                textwrap.dedent(f"""
                <div style="border-bottom: 1px solid var(--border-subtle); padding: 14px 0;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                        <span style="font-weight: 700; font-size: 1rem; color: var(--text-primary);">{skill_name}</span>
                        <span class="tf-tag tf-tag-neutral">{category}</span>
                    </div>
                    <div style="font-size: 0.82rem; font-weight: 600; color: var(--text-secondary); margin-top: 6px;">What to learn:</div>
                    <div style="margin-top: 2px; margin-bottom: 8px;">{topics_html}</div>
                    
                    <div style="background-color: var(--bg-surface-alt); padding: 10px 12px; border-radius: 4px; border: 1px solid var(--border-subtle); margin-top: 6px; margin-bottom: 8px;">
                        <div style="font-size: 0.78rem; font-weight: 600; color: var(--text-muted); margin-bottom: 4px;">How to practice (Learning Sequence):</div>
                        {seq_html}
                    </div>

                    <div style="background-color: var(--bg-surface-alt); padding: 8px 10px; border-radius: 4px; border: 1px solid var(--border-subtle); margin-bottom: 8px;">
                        <div style="font-size: 0.75rem; font-weight: 600; color: var(--text-muted);">Suggested Practice Project:</div>
                        <div style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 2px;">{practice_project}</div>
                    </div>
                    
                    <div style="font-size: 0.75rem; font-weight: 600; color: var(--text-muted); margin-top: 6px;">Useful search phrases:</div>
                    <div style="margin-top: 2px; margin-bottom: 6px;">{search_html}</div>

                    <div style="font-size: 0.75rem; font-weight: 600; color: var(--text-muted); margin-top: 4px;">Resource types:</div>
                    <div style="margin-top: 2px;">{resources_html}</div>
                </div>
                """).strip(),
                unsafe_allow_html=True
            )
            
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # 8. Final Candidate Guidance Conclusion
    st.markdown(
        textwrap.dedent("""
        <div class="tf-card" style="border-left: 4px solid #10B981; background-color: var(--bg-surface-alt); padding: 14px 16px;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #10B981; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
                💡 Final Candidate Guidance
            </div>
            <div style="font-size: 0.9rem; color: var(--text-primary); line-height: 1.6;">
                Your biggest opportunity is to add or demonstrate the missing skills that you genuinely have experience with, then update the relevant resume sections. For skills you do not yet know, use the learning plan above before claiming them on your resume.
            </div>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )

    # Bottom Action Bar
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    bot_c1, bot_c2, _ = st.columns([1.5, 1.5, 3])
    with bot_c1:
        if st.button("← Modify Inputs & Re-run", key="btn_rerun_js", type="primary", use_container_width=True):
            navigate_to(Routes.JOB_SEEKER)
            st.rerun()
    with bot_c2:
        if st.button("Explore Recruiter View", key="btn_go_to_rec", type="secondary", use_container_width=True):
            navigate_to(Routes.RECRUITER)
            st.rerun()
