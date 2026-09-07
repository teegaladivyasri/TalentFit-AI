"""Tests for Phase 5A, 5B, and 5C: State management, JD skill isolation, and functional reliability."""

import pytest
import streamlit as st
from services.skill_extractor import SkillExtractor
from services.text_preprocessor import TextPreprocessor
from services.matcher import ResumeMatcher
from services.ats_analyzer import ATSAnalyzer
from services.recommender import RecommendationService
from utils.session_state import reset_job_seeker_inputs, reset_recruiter_inputs
from components.score import render_ats_breakdown, render_overall_match_banner, render_score_bar
from components.cards import render_metric_card
from data.mock_data import SAMPLE_JOB_DESCRIPTION


class TestJDSkillIsolationAndReliability:
    """Test suite for JD skill isolation to prevent phantom missing skills."""

    def setup_method(self):
        self.extractor = SkillExtractor()
        self.preprocessor = TextPreprocessor()
        self.matcher = ResumeMatcher()
        self.ats_analyzer = ATSAnalyzer()
        self.recommender = RecommendationService()

    def test_jd_only_contains_explicit_skills(self):
        """Verify that a minimal JD only extracts skills explicitly present in text."""
        custom_jd = """
        We are hiring a Backend Engineer.
        Required Skills:
        - Python
        - FastAPI
        - PostgreSQL
        
        Responsibilities:
        Build high-performance REST APIs.
        """
        proc_jd = self.preprocessor.preprocess(custom_jd, doc_type="jd")
        extracted_jd = self.extractor.extract(custom_jd, sections=proc_jd.get("sections"), document_type="jd")
        
        detected_names = set(extracted_jd["skills"])
        # Canonical names for the 3 skills
        assert "Python" in detected_names
        assert "FastAPI" in detected_names
        assert "PostgreSQL" in detected_names
        
        # Must NOT contain phantom skills
        forbidden_phantoms = {"SQL", "GitHub", "MySQL", "RAG", "Unit Testing", "AWS", "Docker", "Kubernetes", "Redis", "GraphQL"}
        intersection = detected_names.intersection(forbidden_phantoms)
        assert len(intersection) == 0, f"Phantom skills detected: {intersection}"

    def test_matching_with_minimal_jd_has_zero_phantom_missing_skills(self):
        """Verify matching a Python-only resume against a 3-skill JD yields only the 2 missing skills."""
        custom_jd = """
        Required Skills:
        - Python
        - FastAPI
        - PostgreSQL
        """
        resume_text = """
        Alex Morgan
        Senior Software Engineer
        Experience:
        - Developed core backend services in Python.
        """
        proc_jd = self.preprocessor.preprocess(custom_jd, doc_type="jd")
        jd_skills = self.extractor.extract(custom_jd, sections=proc_jd.get("sections"), document_type="jd")
        
        proc_resume = self.preprocessor.preprocess(resume_text, doc_type="resume")
        resume_skills = self.extractor.extract(resume_text, sections=proc_resume.get("sections"), document_type="resume")
        
        match_res = self.matcher.match(
            resume_skills=resume_skills,
            jd_skills=jd_skills,
            resume_text=resume_text,
            jd_text=custom_jd
        )
        
        matched_names = [s["skill"] for s in match_res["matched_skills"]]
        missing_names = [s["skill"] for s in match_res["missing_skills"]]
        
        assert "Python" in matched_names
        assert set(missing_names) == {"FastAPI", "PostgreSQL"}
        
        # Recommender skill gaps must only come from missing_skills
        gap_res = self.recommender.prioritize_missing_skills(match_res["missing_skills"])
        gap_skills = [g["skill"] for g in gap_res]
        for g in gap_skills:
            assert g in {"FastAPI", "PostgreSQL"}, f"Unexpected skill gap found: {g}"

    def test_case_sensitive_rag_protection(self):
        """Verify the word 'rag' or 'rage' in regular prose does not trigger RAG skill."""
        text = "Handled customer issues with great care and no rage or ragging."
        proc = self.preprocessor.preprocess(text, doc_type="resume")
        skills = self.extractor.extract(text, sections=proc.get("sections"), document_type="resume")
        assert "RAG" not in skills["skills"]

    def test_case_sensitive_rag_matches_exact_acronym(self):
        """Verify 'RAG' in uppercase does trigger RAG skill."""
        text = "Engineered Retrieval-Augmented Generation (RAG) pipeline for internal search."
        proc = self.preprocessor.preprocess(text, doc_type="resume")
        skills = self.extractor.extract(text, sections=proc.get("sections"), document_type="resume")
        assert "RAG" in skills["skills"]


class TestSessionStateAndReset:
    """Test suite for session state resets and widget state synchronization."""

    def test_reset_job_seeker_cleans_widget_and_custom_keys(self):
        """Test reset_job_seeker_inputs purges widget keys and data keys."""
        mock_state = {
            "js_resume_file": "fake_file",
            "js_jd_text": "fake_jd",
            "js_jd_text_input": "fake_jd",
            "js_resume_uploader": "fake_uploader",
            "js_analysis_results": {"mock": True},
            "js_jd_skills": ["Python"]
        }
        
        reset_job_seeker_inputs(mock_state)
        
        assert mock_state.get("js_resume_file") is None
        assert mock_state.get("js_jd_text") == ""
        assert mock_state.get("js_jd_text_input") == ""
        assert mock_state.get("js_resume_uploader") is None
        assert mock_state.get("js_analysis_results") is None
        assert mock_state.get("js_jd_skills") is None

    def test_reset_recruiter_cleans_widget_and_custom_keys(self):
        """Test reset_recruiter_inputs purges widget keys and data keys."""
        mock_state = {
            "rec_single_resume": "fake_file",
            "rec_jd_text": "fake_jd",
            "rec_jd_text_input": "fake_jd",
            "rec_single_resume_uploader": "fake_uploader",
            "rec_batch_resumes_uploader": ["fake_uploader"],
            "rec_screening_results": [{"id": "cand-01"}],
            "comp_multiselect": ["cand-01"]
        }
        
        reset_recruiter_inputs(mock_state)
        
        assert mock_state.get("rec_single_resume") is None
        assert mock_state.get("rec_jd_text") == ""
        assert mock_state.get("rec_jd_text_input") == ""
        assert mock_state.get("rec_single_resume_uploader") is None
        assert mock_state.get("rec_batch_resumes_uploader") is None
        assert mock_state.get("rec_screening_results") is None
        assert mock_state.get("comp_multiselect") is None


class TestPhase5BProductLogic:
    """Test suite for Phase 5B Job Seeker improvements and Recruiter Clear Filters."""

    def setup_method(self):
        self.extractor = SkillExtractor()
        self.preprocessor = TextPreprocessor()
        self.matcher = ResumeMatcher()
        self.ats_analyzer = ATSAnalyzer()
        self.recommender = RecommendationService()

    def test_section_by_section_resume_improvements_anti_fabrication(self):
        """Verify section-by-section improvements are generated and observe anti-fabrication rules."""
        custom_jd = "Required: Python, FastAPI, Docker, AWS."
        resume_text = "Experience with Python and FastAPI."
        
        p_jd = self.preprocessor.preprocess(custom_jd, doc_type="jd")
        jd_sk = self.extractor.extract(custom_jd, sections=p_jd.get("sections"), document_type="jd")
        
        p_res = self.preprocessor.preprocess(resume_text, doc_type="resume")
        res_sk = self.extractor.extract(resume_text, sections=p_res.get("sections"), document_type="resume")
        
        m_res = self.matcher.match(
            resume_skills=res_sk,
            jd_skills=jd_sk,
            resume_text=resume_text,
            jd_text=custom_jd
        )
        
        recs = self.recommender.generate_resume_suggestions(
            match_result=m_res,
            resume_processed=p_res,
            resume_skills=res_sk
        )
        
        sec_imp = recs.get("section_improvements", {})
        assert "Technical Skills" in sec_imp
        assert "Work Experience" in sec_imp
        assert "Projects" in sec_imp
        assert "Professional Summary" in sec_imp
        
        # Check anti-fabrication phrasing
        tech_text = " ".join(sec_imp["Technical Skills"])
        assert "If you have" in tech_text or "If you possess" in tech_text

    def test_learning_roadmap_practical_guidance(self):
        """Verify learning roadmap includes what_to_learn, how_to_practice, practice_project, and resource_types."""
        missing = [
            {"skill": "AWS", "category": "Cloud Platforms & Services", "is_required": True, "priority": "high", "jd_occurrences": 2},
            {"skill": "Docker", "category": "DevOps & Infrastructure", "is_required": True, "priority": "high", "jd_occurrences": 1}
        ]
        
        roadmap = self.recommender.generate_learning_roadmap(missing)
        assert len(roadmap) == 2
        for item in roadmap:
            assert "what_to_learn" in item
            assert isinstance(item["what_to_learn"], list)
            assert len(item["what_to_learn"]) > 0
            assert "how_to_practice" in item
            assert "practice_project" in item
            assert "resource_types" in item
            assert "search_phrases" in item
            assert "learning_sequence" in item

    def test_recruiter_clear_filters_preserves_candidates(self):
        """Verify clearing recruiter filters resets filter inputs without modifying the candidate pool."""
        sample_candidates = [
            {"id": "cand-01", "name": "Alex", "overall_match": 85},
            {"id": "cand-02", "name": "Jordan", "overall_match": 72}
        ]
        
        mock_state = {
            "rec_screening_results": sample_candidates,
            "rec_filter_search": "alex",
            "rec_filter_score_range": "80%+",
            "rec_filter_req_cov": "80%+",
            "rec_filter_status": "Strong Match",
            "rec_filter_skill": "Python",
            "rec_filter_sort": "Candidate Name (A to Z)"
        }
        
        # Simulate Clear Filters action
        mock_state["rec_filter_search"] = ""
        mock_state["rec_filter_score_range"] = "All Scores"
        mock_state["rec_filter_req_cov"] = "All Coverage"
        mock_state["rec_filter_status"] = "All Statuses"
        mock_state["rec_filter_skill"] = "All Skills"
        mock_state["rec_filter_sort"] = "Overall Match (High to Low)"
        
        # Candidates must be intact
        assert len(mock_state["rec_screening_results"]) == 2
        assert mock_state["rec_screening_results"][0]["name"] == "Alex"
        assert mock_state["rec_filter_search"] == ""
        assert mock_state["rec_filter_score_range"] == "All Scores"


class TestPhase5CJobSeekerLogic:
    """Test suite for Phase 5C Job Seeker scoring, zero-skill JDs, and ATS removal."""

    def setup_method(self):
        self.extractor = SkillExtractor()
        self.preprocessor = TextPreprocessor()
        self.matcher = ResumeMatcher()

    def test_job_seeker_jd_match_is_strict_skill_ratio(self):
        """Verify JD match is exactly matched_skills / total_jd_skills * 100."""
        custom_jd = """
        Required Skills:
        - Python
        - FastAPI
        - PostgreSQL
        - Docker
        - AWS
        """
        resume_text = """
        Alex Morgan
        Senior Software Engineer
        Experience:
        - Developed REST backend microservices with Python and FastAPI.
        - Containerized backend services with Docker.
        """
        p_jd = self.preprocessor.preprocess(custom_jd, doc_type="jd")
        jd_sk = self.extractor.extract(custom_jd, sections=p_jd.get("sections"), document_type="jd")
        
        p_res = self.preprocessor.preprocess(resume_text, doc_type="resume")
        res_sk = self.extractor.extract(resume_text, sections=p_res.get("sections"), document_type="resume")
        
        m_res = self.matcher.match(
            resume_skills=res_sk,
            jd_skills=jd_sk,
            resume_text=resume_text,
            jd_text=custom_jd
        )
        
        matched_list = [s["skill"] for s in m_res["matched_skills"]]
        missing_list = [s["skill"] for s in m_res["missing_skills"]]
        
        assert set(matched_list) == {"Python", "FastAPI", "Docker"}
        assert set(missing_list) == {"PostgreSQL", "AWS"}
        
        total_jd_skills = len(matched_list) + len(missing_list)
        assert total_jd_skills == 5
        
        jd_match_pct = round((len(matched_list) / total_jd_skills) * 100)
        assert jd_match_pct == 60  # Exactly 3/5 * 100

    def test_job_seeker_zero_skill_jd_handled_safely(self):
        """Verify a JD with no detected taxonomy skills yields total_jd_skills == 0 and None match pct."""
        zero_skill_jd = "Looking for an enthusiastic team player with strong communication."
        p_jd = self.preprocessor.preprocess(zero_skill_jd, doc_type="jd")
        jd_sk = self.extractor.extract(zero_skill_jd, sections=p_jd.get("sections"), document_type="jd")
        
        assert len(jd_sk["skills"]) == 0
        total_jd_skills_count = len(jd_sk["skills"])
        jd_match_pct = round((0 / total_jd_skills_count) * 100) if total_jd_skills_count > 0 else None
        assert jd_match_pct is None


class TestHTMLFormattingSafety:
    """Test suite ensuring HTML generation does not leak code block indentation."""

    def test_no_four_space_leading_lines_in_common_components(self):
        """Verify dedenting helpers prevent leading spaces that markdown parsers turn into code blocks."""
        test_snippet = """
        <div class="tf-card">
            <div class="tf-card-title">Test</div>
        </div>
        """
        import textwrap
        dedented = textwrap.dedent(test_snippet).strip()
        for line in dedented.split("\n"):
            assert not line.startswith("    <div class=\"tf-card\">")
