"""Recruiter Workflow: Job Description & Candidate Upload Hub."""

import textwrap
import streamlit as st
from utils.constants import Routes, RecruiterMode, CandidateStatus, ALLOWED_JD_EXTENSIONS
from utils.session_state import navigate_to, reset_recruiter_inputs
from utils.validators import (
    validate_job_description, 
    validate_resume_file, 
    validate_batch_resumes
)
from data.mock_data import (
    SAMPLE_JOB_DESCRIPTION, 
    get_mock_recruiter_candidates, 
    get_candidate_by_id
)
from services.document_parser import DocumentParser
from services.text_preprocessor import TextPreprocessor
from services.skill_extractor import SkillExtractor
from services.matcher import ResumeMatcher
from components.upload import render_resume_uploader, render_batch_uploader
from components.cards import render_callout


def _on_rec_load_sample_jd() -> None:
    """Safely populate sample JD in recruiter mode before widget rendering."""
    st.session_state["rec_jd_text"] = SAMPLE_JOB_DESCRIPTION
    st.session_state["rec_jd_text_input"] = SAMPLE_JOB_DESCRIPTION
    st.session_state["rec_jd_file"] = None
    st.session_state["rec_jd_mode"] = "paste"


def _on_rec_reset() -> None:
    """Safely reset all recruiter state and widgets before rendering."""
    reset_recruiter_inputs()


def render_recruiter_page() -> None:
    """Render the Recruiter Job Description input and screening mode selector."""
    
    # Header
    st.markdown(
        textwrap.dedent("""
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 1.75rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.02em;">Candidate Screening</div>
            <div style="font-size: 0.95rem; color: var(--text-secondary); margin-top: 4px;">
                Evaluate and benchmark candidate resumes against target role requirements.
            </div>
        </div>
        """), 
        unsafe_allow_html=True
    )
    
    # 1. Job Description Section
    st.markdown(
        textwrap.dedent("""
        <div class="tf-card">
            <div class="tf-card-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="tf-step-badge">1</span>
                    <div class="tf-card-title">Target Role & Job Description</div>
                </div>
            </div>
            <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">
                Specify the requirements against which candidate resumes will be benchmarked.
            </div>
        """),
        unsafe_allow_html=True
    )
    
    tab_paste, tab_upload = st.tabs(["📝 Paste Job Description", "📁 Upload JD Document"])
    
    with tab_paste:
        if "rec_jd_text_input" not in st.session_state:
            st.session_state["rec_jd_text_input"] = st.session_state.get("rec_jd_text", "")
            
        jd_text = st.text_area(
            label="Target Job Description Text",
            placeholder="Paste role requirements, tech stack, and responsibilities...",
            height=160,
            key="rec_jd_text_input"
        )
        st.session_state["rec_jd_text"] = jd_text
        st.session_state["rec_jd_mode"] = "paste"
        
        st.button(
            "Load Standard Senior Engineer Spec", 
            key="rec_load_sample_jd", 
            type="secondary",
            on_click=_on_rec_load_sample_jd
        )

    with tab_upload:
        jd_file = st.file_uploader(
            label="Upload Job Description File",
            type=ALLOWED_JD_EXTENSIONS,
            key="rec_jd_file_input",
            label_visibility="collapsed"
        )
        if jd_file:
            st.session_state["rec_jd_file"] = jd_file
            st.session_state["rec_jd_mode"] = "upload"
            st.markdown(
                f"<div style='font-size: 0.85rem; color: var(--text-primary); margin-top: 8px;'>Attached Spec: <strong>{jd_file.name}</strong></div>", 
                unsafe_allow_html=True
            )
            
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # 2. Screening Mode Selector
    st.markdown(
        """
        <div class="tf-card">
            <div class="tf-card-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="tf-step-badge">2</span>
                    <div class="tf-card-title">Choose Screening Mode</div>
                </div>
            </div>
        """,
        unsafe_allow_html=True
    )
    
    mode_col1, mode_col2 = st.columns(2, gap="medium")
    curr_mode = st.session_state.get("rec_screening_mode", RecruiterMode.BATCH)
    
    with mode_col1:
        is_single = (curr_mode == RecruiterMode.SINGLE)
        st.markdown(
            f"""
            <div style="border: 2px solid {'#2563EB' if is_single else 'var(--border-subtle)'}; background-color: var(--bg-surface-alt); padding: 14px; border-radius: 6px; margin-bottom: 8px;">
                <div style="font-weight: 600; color: var(--text-primary);">Single Candidate Analysis</div>
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">Deep dive evaluation of a specific individual candidate resume.</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        if st.button("Select Single Candidate Mode", key="btn_mode_single", type="primary" if is_single else "secondary", use_container_width=True):
            st.session_state["rec_screening_mode"] = RecruiterMode.SINGLE
            st.rerun()

    with mode_col2:
        is_batch = (curr_mode == RecruiterMode.BATCH)
        st.markdown(
            f"""
            <div style="border: 2px solid {'#2563EB' if is_batch else 'var(--border-subtle)'}; background-color: var(--bg-surface-alt); padding: 14px; border-radius: 6px; margin-bottom: 8px;">
                <div style="font-weight: 600; color: var(--text-primary);">Batch Candidate Screening</div>
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">Upload multiple resumes to generate automated ranked candidate tables.</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        if st.button("Select Batch Screening Mode", key="btn_mode_batch", type="primary" if is_batch else "secondary", use_container_width=True):
            st.session_state["rec_screening_mode"] = RecruiterMode.BATCH
            st.rerun()

    st.markdown("<hr style='margin: 1.25rem 0; border: none; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)

    parser = DocumentParser()
    preprocessor = TextPreprocessor()
    extractor = SkillExtractor()
    matcher = ResumeMatcher()
    from services.ats_analyzer import ATSAnalyzer
    ats_analyzer = ATSAnalyzer()

    def _build_candidate_record(
        cand_id: str,
        filename: str,
        raw_text: str,
        proc_res: dict,
        cand_skills: dict,
        match_result: dict,
        ats_result: dict
    ) -> dict:
        cand_name = parser.extract_candidate_name(text=raw_text, filename=filename)
        
        overall_score = match_result["overall_score"]
        req_cov = round(match_result["required_skill_coverage"], 1)
        skill_score = int(round(match_result["skill_match_score"]))
        sim_score = int(round(match_result["content_similarity_score"]))
        
        matched_req = [s["skill"] for s in match_result["matched_skills"] if s.get("is_required", True)]
        missing_req = [s["skill"] for s in match_result["missing_skills"] if s.get("is_required", True)]
        matched_pref = [s["skill"] for s in match_result["matched_skills"] if not s.get("is_required", True)]
        missing_pref = [s["skill"] for s in match_result["missing_skills"] if not s.get("is_required", True)]
        extra_sk = [s["skill"] for s in match_result["extra_skills"]]
        
        if overall_score >= 80 and req_cov >= 75.0:
            cand_status = "Strong Match"
            rec_note = f"High alignment across core role specifications ({req_cov}% required skills verified). Strong candidate for technical screening."
        elif overall_score >= 65 and req_cov >= 50.0:
            cand_status = "Good Match"
            missing_str = f"Missing {len(missing_req)} required skill(s): {', '.join(missing_req[:2])}" if missing_req else "Minor preferred skill gaps"
            rec_note = f"Good foundational alignment ({overall_score}% overall). {missing_str}."
        elif overall_score >= 45:
            cand_status = "Partial Match"
            missing_str = f"Lacks key requirements: {', '.join(missing_req[:3])}" if missing_req else "Low skill overlap"
            rec_note = f"Partial alignment with role specifications. {missing_str}."
        else:
            cand_status = "Low Match"
            rec_note = f"Significant skill gap detected ({req_cov}% required coverage). Key qualifications not detected in resume."

        return {
            "id": cand_id,
            "rank": 0,
            "name": cand_name,
            "filename": filename,
            "current_title": "Software Engineer",
            "overall_match": overall_score,
            "skill_match": skill_score,
            "content_similarity": sim_score,
            "required_skill_coverage": req_cov,
            "jd_coverage": int(round(req_cov)),
            "status": cand_status,
            "ats_score": ats_result.get("score", 80),
            "ats_breakdown": ats_result.get("components", {}),
            "summary": f"{cand_status} profile with {len(match_result['matched_skills'])} matched skills and {req_cov}% required coverage.",
            "matched_skills": [s["skill"] for s in match_result["matched_skills"]],
            "missing_skills": [s["skill"] for s in match_result["missing_skills"]],
            "extra_skills": extra_sk,
            "matched_required_skills": matched_req,
            "missing_required_skills": missing_req,
            "matched_preferred_skills": matched_pref,
            "missing_preferred_skills": missing_pref,
            "recommendation_note": rec_note,
            "match_result": match_result,
            "ats_result": ats_result,
            "original_text": raw_text,
            "processed": proc_res,
            "extracted_skills": cand_skills,
        }

    # Mode-Specific Upload Controls
    if curr_mode == RecruiterMode.SINGLE:
        st.markdown("#### Single Candidate Resume Upload")
        single_file = render_resume_uploader("rec_single_resume_uploader")
        if single_file:
            st.session_state["rec_single_resume"] = single_file
            st.session_state["rec_single_resume_name"] = single_file.name

        st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)
        
        btn_c1, btn_c2, _ = st.columns([1.5, 1.2, 2.5])
        with btn_c1:
            if st.button("Analyze Candidate", key="btn_run_single_candidate", type="primary", use_container_width=True):
                # 1. Validation
                jd_mode = st.session_state.get("rec_jd_mode", "paste")
                jd_text_val = st.session_state.get("rec_jd_text", "")
                jd_file_val = st.session_state.get("rec_jd_file")
                
                jd_val = validate_job_description(jd_mode, jd_text_val, jd_file_val)
                if not jd_val.is_valid:
                    st.error(jd_val.message)
                    return
                    
                resume_file = st.session_state.get("rec_single_resume")
                resume_val = validate_resume_file(resume_file)
                if not resume_val.is_valid:
                    st.error(resume_val.message)
                    return

                with st.spinner("Screening candidate against role specification..."):
                    # 2. Extract & Preprocess JD text & Skills
                    if jd_mode == "upload":
                        jd_parsed = parser.parse_document(jd_file_val)
                        if jd_parsed["status"] == "error" or not jd_parsed["text"].strip():
                            st.error(jd_parsed.get("error_message") or "Unable to extract readable text from the uploaded Job Description.")
                            return
                        raw_jd = jd_parsed["text"]
                    else:
                        raw_jd = jd_text_val

                    jd_processed = preprocessor.preprocess(raw_jd, doc_type="jd")
                    jd_skills = extractor.extract(raw_jd, sections=jd_processed.get("sections"), document_type="jd")
                    
                    st.session_state["rec_jd_extracted_text"] = raw_jd
                    st.session_state["rec_jd_processed"] = jd_processed
                    st.session_state["rec_jd_skills"] = jd_skills

                    # 3. Extract & Preprocess Resume text & Skills
                    resume_parsed = parser.parse_document(resume_file)
                    if resume_parsed["status"] == "error" or not resume_parsed["text"].strip():
                        st.error(resume_parsed.get("error_message") or "Unable to extract readable text from the candidate resume.")
                        return
                        
                    resume_processed = preprocessor.preprocess(resume_parsed["text"], doc_type="resume")
                    resume_skills = extractor.extract(
                        resume_parsed["text"], 
                        sections=resume_processed.get("sections"), 
                        document_type="resume"
                    )
                    
                    st.session_state["rec_single_resume_text"] = resume_parsed["text"]
                    st.session_state["rec_single_resume_processed"] = resume_processed
                    st.session_state["rec_single_resume_skills"] = resume_skills

                    # 4. Matching & ATS Scoring
                    match_result = matcher.match(
                        resume_skills=resume_skills,
                        jd_skills=jd_skills,
                        resume_text=resume_parsed["text"],
                        jd_text=raw_jd
                    )
                    ats_res = ats_analyzer.analyze(
                        resume_text=resume_parsed["text"],
                        resume_processed=resume_processed,
                        resume_skills=resume_skills
                    )
                    st.session_state["rec_single_match_result"] = match_result

                    # Create structured candidate record
                    resume_file_name = getattr(resume_file, "name", "Candidate_Resume.pdf")
                    single_cand = _build_candidate_record(
                        cand_id="cand-01",
                        filename=resume_file_name,
                        raw_text=resume_parsed["text"],
                        proc_res=resume_processed,
                        cand_skills=resume_skills,
                        match_result=match_result,
                        ats_result=ats_res
                    )
                    single_cand["rank"] = 1
                    st.session_state["rec_screening_results"] = [single_cand]

                    # Route to candidate details
                    st.session_state["rec_selected_candidate_id"] = "cand-01"
                    navigate_to(Routes.CANDIDATE_DETAILS)
                    st.rerun()

        with btn_c2:
            st.button(
                "Reset", 
                key="btn_reset_single", 
                type="secondary", 
                use_container_width=True,
                on_click=_on_rec_reset
            )

    else:
        st.markdown("#### Upload Multiple Resumes")
        batch_files = render_batch_uploader("rec_batch_resumes_uploader")
        if batch_files:
            st.session_state["rec_batch_resumes"] = batch_files
            
        st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)
        
        btn_c1, btn_c2, btn_c3 = st.columns([1.5, 1.8, 1.2])
        with btn_c1:
            if st.button("Analyze & Rank Batch", key="btn_run_batch_ranking", type="primary", use_container_width=True):
                jd_mode = st.session_state.get("rec_jd_mode", "paste")
                jd_text_val = st.session_state.get("rec_jd_text", "")
                jd_file_val = st.session_state.get("rec_jd_file")
                
                jd_val = validate_job_description(jd_mode, jd_text_val, jd_file_val)
                if not jd_val.is_valid:
                    st.error(jd_val.message)
                    return
                    
                uploaded_batch = st.session_state.get("rec_batch_resumes", [])
                if not uploaded_batch:
                    st.error("Please upload at least one candidate resume for batch screening (or click 'Use Pre-populated 5 Candidate Pool' below).")
                    return

                with st.spinner("Processing candidate batch and computing rankings..."):
                    # Extract & Preprocess JD text
                    if jd_mode == "upload":
                        jd_parsed = parser.parse_document(jd_file_val)
                        if jd_parsed["status"] == "error" or not jd_parsed["text"].strip():
                            st.error(jd_parsed.get("error_message") or "Unable to extract readable text from the uploaded Job Description.")
                            return
                        raw_jd = jd_parsed["text"]
                    else:
                        raw_jd = jd_text_val

                    jd_processed = preprocessor.preprocess(raw_jd, doc_type="jd")
                    jd_skills = extractor.extract(raw_jd, sections=jd_processed.get("sections"), document_type="jd")
                    
                    st.session_state["rec_jd_extracted_text"] = raw_jd
                    st.session_state["rec_jd_processed"] = jd_processed
                    st.session_state["rec_jd_skills"] = jd_skills

                    # Extract, Preprocess, and Match batch candidate texts and skills
                    extracted_candidates = []
                    screened_candidates = []
                    extraction_errors = []

                    for i, f in enumerate(uploaded_batch):
                        p_res = parser.parse_document(f)
                        if p_res["status"] == "error" or not p_res["text"].strip():
                            extraction_errors.append(f"{f.name}: {p_res.get('error_message', 'No readable text')}")
                        else:
                            proc_res = preprocessor.preprocess(p_res["text"], doc_type="resume")
                            cand_skills = extractor.extract(
                                p_res["text"], 
                                sections=proc_res.get("sections"), 
                                document_type="resume"
                            )
                            cand_id = f"cand-{i+1:02d}"
                            extracted_candidates.append({
                                "id": cand_id,
                                "filename": f.name,
                                "original_text": p_res["text"],
                                "processed": proc_res,
                                "extracted_skills": cand_skills,
                                "char_count": p_res["char_count"],
                                "word_count": p_res["word_count"],
                                "token_count": proc_res["token_count"],
                                "page_count": p_res["page_count"],
                                "status": "extracted"
                            })

                            # Deterministic matching
                            cand_match = matcher.match(
                                resume_skills=cand_skills,
                                jd_skills=jd_skills,
                                resume_text=p_res["text"],
                                jd_text=raw_jd
                            )
                            ats_res = ats_analyzer.analyze(
                                resume_text=p_res["text"],
                                resume_processed=proc_res,
                                resume_skills=cand_skills
                            )
                            
                            cand_record = _build_candidate_record(
                                cand_id=cand_id,
                                filename=f.name,
                                raw_text=p_res["text"],
                                proc_res=proc_res,
                                cand_skills=cand_skills,
                                match_result=cand_match,
                                ats_result=ats_res
                            )
                            screened_candidates.append(cand_record)

                    if not extracted_candidates:
                        st.error("None of the uploaded candidate resumes contained readable text. Issues: " + "; ".join(extraction_errors))
                        return

                    if extraction_errors:
                        st.warning(f"Note: {len(extraction_errors)} file(s) had extraction issues: " + "; ".join(extraction_errors))

                    # Deterministic ranking: highest overall_match first, then tie-break by name, then id
                    screened_candidates.sort(key=lambda c: (-c["overall_match"], c["name"].lower(), c["id"]))
                    for rank_idx, c in enumerate(screened_candidates, start=1):
                        c["rank"] = rank_idx

                    st.session_state["rec_batch_extracted_candidates"] = extracted_candidates
                    st.session_state["rec_screening_results"] = screened_candidates
                    st.session_state["rec_compared_candidate_ids"] = [c["id"] for c in screened_candidates[:2]]
                    navigate_to(Routes.RECRUITER_SCREENING)
                    st.rerun()
                
        with btn_c2:
            if st.button("⚡ Use Sample 5 Candidate Pool", key="btn_load_sample_batch", type="secondary", use_container_width=True):
                from tests.fixtures.synthetic_resumes import (
                    RESUME_A_STRONG_MATCH,
                    RESUME_B_MODERATE_MATCH,
                    RESUME_C_WEAK_MATCH,
                    RESUME_D_EXTRA_SKILLS,
                    RESUME_E_ALIAS_HEAVY,
                    JD_1_PYTHON_BACKEND
                )
                raw_jd = JD_1_PYTHON_BACKEND
                st.session_state["rec_jd_text"] = raw_jd
                st.session_state["rec_jd_extracted_text"] = raw_jd
                jd_proc = preprocessor.preprocess(raw_jd, doc_type="jd")
                jd_skills = extractor.extract(raw_jd, sections=jd_proc.get("sections"), document_type="jd")
                st.session_state["rec_jd_processed"] = jd_proc
                st.session_state["rec_jd_skills"] = jd_skills

                sample_resumes = [
                    ("Alex_Morgan_Resume.pdf", RESUME_A_STRONG_MATCH),
                    ("Jordan_Lee_Resume.pdf", RESUME_B_MODERATE_MATCH),
                    ("Samantha_Taylor_Resume.pdf", RESUME_C_WEAK_MATCH),
                    ("David_Chen_Resume.pdf", RESUME_D_EXTRA_SKILLS),
                    ("Marcus_Vance_Resume.pdf", RESUME_E_ALIAS_HEAVY),
                ]

                screened = []
                for i, (fname, rtext) in enumerate(sample_resumes):
                    cand_id = f"cand-{i+1:02d}"
                    r_proc = preprocessor.preprocess(rtext, doc_type="resume")
                    r_sk = extractor.extract(rtext, sections=r_proc.get("sections"), document_type="resume")
                    m_res = matcher.match(
                        resume_skills=r_sk,
                        jd_skills=jd_skills,
                        resume_text=rtext,
                        jd_text=raw_jd
                    )
                    ats_res = ats_analyzer.analyze(
                        resume_text=rtext,
                        resume_processed=r_proc,
                        resume_skills=r_sk
                    )
                    cand_rec = _build_candidate_record(
                        cand_id=cand_id,
                        filename=fname,
                        raw_text=rtext,
                        proc_res=r_proc,
                        cand_skills=r_sk,
                        match_result=m_res,
                        ats_result=ats_res
                    )
                    screened.append(cand_rec)

                screened.sort(key=lambda c: (-c["overall_match"], c["name"].lower(), c["id"]))
                for rank_idx, c in enumerate(screened, start=1):
                    c["rank"] = rank_idx

                st.session_state["rec_screening_results"] = screened
                st.session_state["rec_compared_candidate_ids"] = [c["id"] for c in screened[:2]]
                navigate_to(Routes.RECRUITER_SCREENING)
                st.rerun()

        with btn_c3:
            st.button(
                "Reset", 
                key="btn_reset_batch", 
                type="secondary", 
                use_container_width=True,
                on_click=_on_rec_reset
            )

    st.markdown("</div>", unsafe_allow_html=True)
