"""Job Seeker Workflow: Resume & Job Description Upload Page."""

import streamlit as st
from utils.constants import Routes, ALLOWED_JD_EXTENSIONS
from utils.session_state import navigate_to, reset_job_seeker_inputs
from utils.validators import validate_resume_file, validate_job_description
from data.mock_data import SAMPLE_JOB_DESCRIPTION
from services.document_parser import DocumentParser
from services.text_preprocessor import TextPreprocessor
from services.skill_extractor import SkillExtractor
from services.matcher import ResumeMatcher
from services.ats_analyzer import ATSAnalyzer
from services.recommender import RecommendationService
from components.upload import render_resume_uploader
from components.cards import render_callout


def _on_load_sample_jd() -> None:
    """Callback triggered before widget rendering to safely populate sample JD without instantiation error."""
    st.session_state["js_jd_text"] = SAMPLE_JOB_DESCRIPTION
    st.session_state["js_jd_text_input"] = SAMPLE_JOB_DESCRIPTION
    st.session_state["js_jd_mode"] = "paste"
    st.session_state["js_jd_file"] = None


def _on_reset_job_seeker() -> None:
    """Callback triggered before widget rendering to completely reset job seeker state and form fields."""
    reset_job_seeker_inputs()


def render_job_seeker_page() -> None:
    """Render the Job Seeker input page."""
    
    # Page Header
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 1.75rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.02em;">Analyze Your Resume</div>
            <div style="font-size: 0.95rem; color: var(--text-secondary); margin-top: 4px;">
                See how closely your current skills match a job and what you can improve before applying.
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    col_left, col_right = st.columns(2, gap="large")
    
    # Left Card: Resume Upload
    with col_left:
        st.markdown(
            """
            <div class="tf-card" style="height: 100%;">
                <div class="tf-card-header">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="tf-step-badge">1</span>
                        <div class="tf-card-title">Upload Resume</div>
                    </div>
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">
                    Upload your current resume document to extract skills and experience.
                </div>
            """, 
            unsafe_allow_html=True
        )
        
        uploaded_resume = render_resume_uploader("js_resume_uploader")
        if uploaded_resume:
            st.session_state["js_resume_file"] = uploaded_resume
            st.session_state["js_resume_name"] = uploaded_resume.name
            
        st.markdown("</div>", unsafe_allow_html=True)
        
    # Right Card: Job Description Input
    with col_right:
        st.markdown(
            """
            <div class="tf-card" style="height: 100%;">
                <div class="tf-card-header">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="tf-step-badge">2</span>
                        <div class="tf-card-title">Job Description</div>
                    </div>
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">
                    Paste the target job posting text or upload the job specification document.
                </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Tabs for Paste vs Upload JD
        tab_paste, tab_upload = st.tabs(["📝 Paste Job Description", "📁 Upload JD"])
        
        with tab_paste:
            # Initialize state key if not present
            if "js_jd_text_input" not in st.session_state:
                st.session_state["js_jd_text_input"] = st.session_state.get("js_jd_text", "")
                
            jd_text_val = st.text_area(
                label="Job Description Text",
                placeholder="Paste the full job posting, tech stack, and responsibilities here...",
                height=180,
                key="js_jd_text_input"
            )
            st.session_state["js_jd_text"] = jd_text_val
            st.session_state["js_jd_mode"] = "paste"
            
            # Use on_click callback for robust state updates
            st.button(
                "Load Sample Full-Stack JD", 
                key="js_load_sample_jd", 
                type="secondary",
                on_click=_on_load_sample_jd
            )
                
        with tab_upload:
            uploaded_jd = st.file_uploader(
                label="Upload JD file",
                type=ALLOWED_JD_EXTENSIONS,
                key="js_jd_file_uploader",
                label_visibility="collapsed"
            )
            if uploaded_jd:
                st.session_state["js_jd_file"] = uploaded_jd
                st.session_state["js_jd_mode"] = "upload"
                st.markdown(
                    f"""
                    <div style="font-size: 0.85rem; color: var(--text-primary); margin-top: 8px;">
                        Attached Spec: <strong>{uploaded_jd.name}</strong>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin: 1.5rem 0; border: none; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)
    
    # Action Toolbar
    act_col1, act_col2, act_col3 = st.columns([1.5, 1.2, 2.5])
    
    with act_col1:
        if st.button("Analyze Resume", key="btn_run_js_analysis", type="primary", use_container_width=True):
            # 1. Validation checks
            resume_file = st.session_state.get("js_resume_file")
            resume_val = validate_resume_file(resume_file)
            if not resume_val.is_valid:
                st.error(resume_val.message)
                return
                
            jd_mode = st.session_state.get("js_jd_mode", "paste")
            jd_text = st.session_state.get("js_jd_text", "")
            jd_file = st.session_state.get("js_jd_file")
            jd_val = validate_job_description(jd_mode, jd_text, jd_file)
            if not jd_val.is_valid:
                st.error(jd_val.message)
                return

            with st.spinner("Analyzing resume against job requirements..."):
                # 2. Real Document Extraction & NLP Preprocessing
                parser = DocumentParser()
                preprocessor = TextPreprocessor()
                extractor = SkillExtractor()
                
                # Resume Processing
                resume_parsed = parser.parse_document(resume_file)
                if resume_parsed["status"] == "error" or not resume_parsed["text"].strip():
                    st.error(resume_parsed.get("error_message") or "Unable to extract readable text from the uploaded resume. Please check the file contents.")
                    return
                    
                resume_processed = preprocessor.preprocess(resume_parsed["text"], doc_type="resume")
                resume_skills = extractor.extract(
                    text=resume_parsed["text"],
                    sections=resume_processed.get("sections"),
                    document_type="resume"
                )
                
                st.session_state["js_resume_text"] = resume_parsed["text"]
                st.session_state["js_resume_processed"] = resume_processed
                st.session_state["js_resume_skills"] = resume_skills

                # Job Description Processing
                if jd_mode == "upload":
                    jd_parsed = parser.parse_document(jd_file)
                    if jd_parsed["status"] == "error" or not jd_parsed["text"].strip():
                        st.error(jd_parsed.get("error_message") or "Unable to extract readable text from the uploaded Job Description file.")
                        return
                    raw_jd = jd_parsed["text"]
                else:
                    raw_jd = jd_text
                    
                jd_processed = preprocessor.preprocess(raw_jd, doc_type="jd")
                jd_skills = extractor.extract(
                    text=raw_jd,
                    sections=jd_processed.get("sections"),
                    document_type="jd"
                )
                
                st.session_state["js_jd_extracted_text"] = raw_jd
                st.session_state["js_jd_processed"] = jd_processed
                st.session_state["js_jd_skills"] = jd_skills
                    
                # 3. Real Resume-JD Matching & Scoring
                matcher = ResumeMatcher()
                match_result = matcher.match(
                    resume_skills=resume_skills,
                    jd_skills=jd_skills,
                    resume_text=resume_parsed["text"],
                    jd_text=raw_jd
                )
                st.session_state["js_match_result"] = match_result

                # 4. Real ATS Analysis
                ats_analyzer = ATSAnalyzer()
                ats_result = ats_analyzer.analyze(
                    resume_text=resume_parsed["text"],
                    resume_processed=resume_processed,
                    resume_skills=resume_skills
                )
                st.session_state["js_ats_result"] = ats_result

                # 5. Career Guidance & Recommendation Engine
                recommender = RecommendationService(ats_analyzer=ats_analyzer)
                guidance_result = recommender.generate(
                    match_result=match_result,
                    resume_processed=resume_processed,
                    resume_skills=resume_skills,
                    jd_processed=jd_processed,
                    jd_skills=jd_skills,
                    ats_result=ats_result
                )
                st.session_state["js_recommendations"] = guidance_result.get("detailed_recommendations", [])
                st.session_state["js_learning_roadmap"] = guidance_result.get("learning_roadmap", [])
                st.session_state["js_guidance_summary"] = guidance_result.get("guidance_summary", {})

                # 6. Populate analysis results
                resume_name = getattr(resume_file, "name", "My_Resume.pdf")
                extracted_cand_name = parser.extract_candidate_name(resume_parsed["text"], filename=resume_name)
                
                matched_list = [s["skill"] for s in match_result["matched_skills"]]
                missing_list = [s["skill"] for s in match_result["missing_skills"]]
                extra_list = [s["skill"] for s in match_result["extra_skills"]]
                total_jd_skills_count = len(matched_list) + len(missing_list)
                
                if total_jd_skills_count > 0:
                    jd_match_pct = int(round((len(matched_list) / total_jd_skills_count) * 100))
                else:
                    jd_match_pct = None

                analysis_data = {
                    "candidate_name": extracted_cand_name,
                    "resume_filename": resume_name,
                    "target_role": "Target Role Requirements",
                    "target_company": "Target Employer",
                    "jd_match_percentage": jd_match_pct,
                    "total_jd_skills_count": total_jd_skills_count,
                    "scores": {
                        "overall_match": match_result["overall_score"],
                        "skill_match": int(round(match_result["skill_match_score"])),
                        "content_similarity": int(round(match_result["content_similarity_score"])),
                        "jd_coverage": int(round(match_result["required_skill_coverage"])),
                        "ats_score": ats_result["score"],
                        "jd_match": jd_match_pct
                    },
                    "skills": {
                        "matched": matched_list,
                        "missing": missing_list,
                        "extra": extra_list
                    },
                    "resume_strengths": guidance_result.get("resume_strengths", []),
                    "resume_improvements": guidance_result.get("resume_improvements", []),
                    "section_improvements": guidance_result.get("section_improvements", {}),
                    "skills_to_learn": guidance_result.get("learning_roadmap", []),
                    "prioritized_skill_gaps": guidance_result.get("prioritized_skill_gaps", []),
                    "guidance_summary": guidance_result.get("guidance_summary", {}),
                    "match_details": match_result,
                    "ats_details": ats_result
                }
                st.session_state["js_analysis_results"] = analysis_data
                
            navigate_to(Routes.JOB_SEEKER_RESULTS)
            st.rerun()
            
    with act_col2:
        st.button(
            "Reset Form", 
            key="btn_reset_js", 
            type="secondary", 
            use_container_width=True,
            on_click=_on_reset_job_seeker
        )
            
    with act_col3:
        render_callout("Tip: For best results, ensure both core technical competencies and specific tool names are mentioned in your resume.", "info")
