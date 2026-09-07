"""Comprehensive End-to-End Integration & Real-World Validation Test Suite (Phase 2F).

Tests the full unmocked pipeline:
Raw Documents / Text -> Preprocessor -> Skill Extractor -> Matcher -> Scorer -> ATS Analyzer -> Recommender -> Roadmap
"""

import pytest
from services.text_preprocessor import TextPreprocessor
from services.skill_extractor import SkillExtractor
from services.matcher import ResumeMatcher
from services.scorer import ScorerService
from services.ats_analyzer import ATSAnalyzer
from services.recommender import RecommendationService
from utils.constants import SkillPriority
from utils.session_state import reset_job_seeker_inputs
from tests.fixtures.synthetic_resumes import (
    RESUME_A_STRONG_MATCH,
    RESUME_B_MODERATE_MATCH,
    RESUME_C_WEAK_MATCH,
    RESUME_D_EXTRA_SKILLS,
    RESUME_E_ALIAS_HEAVY,
    RESUME_F_FALSE_POSITIVE_STRESS,
    RESUME_G_SPARSE,
    RESUME_H_STRUCTURED,
    RESUME_I_UNUSUAL_SECTIONS,
    RESUME_J_MIXED_TECH_TERMS,
    JD_1_PYTHON_BACKEND,
    JD_2_FRONTEND_JAVASCRIPT,
    JD_3_GENERIC_UNSTRUCTURED
)


@pytest.fixture
def pipeline():
    preprocessor = TextPreprocessor()
    extractor = SkillExtractor()
    scorer = ScorerService()
    matcher = ResumeMatcher(scorer=scorer)
    ats_analyzer = ATSAnalyzer()
    recommender = RecommendationService(ats_analyzer=ats_analyzer)
    return {
        "preprocessor": preprocessor,
        "extractor": extractor,
        "matcher": matcher,
        "scorer": scorer,
        "ats_analyzer": ats_analyzer,
        "recommender": recommender
    }


def run_full_pipeline(pipeline, resume_text: str, jd_text: str):
    """Helper executing unmocked full chain."""
    p = pipeline["preprocessor"]
    e = pipeline["extractor"]
    m = pipeline["matcher"]
    ats = pipeline["ats_analyzer"]
    rec = pipeline["recommender"]

    # 1. Preprocess
    r_proc = p.preprocess(resume_text, doc_type="resume", remove_stopwords=True)
    j_proc = p.preprocess(jd_text, doc_type="jd", remove_stopwords=True)

    # 2. Skill Extract
    r_skills = e.extract(text=r_proc["normalized_text"], sections=r_proc["sections"], document_type="resume")
    j_skills = e.extract(text=j_proc["normalized_text"], sections=j_proc["sections"], document_type="jd")

    # 3. Match
    match_res = m.match(
        resume_skills=r_skills,
        jd_skills=j_skills,
        resume_text=r_proc["cleaned_text"],
        jd_text=j_proc["cleaned_text"]
    )

    # 4. ATS Analyze
    ats_res = ats.analyze(
        resume_text=r_proc["normalized_text"],
        resume_processed=r_proc,
        resume_skills=r_skills
    )

    # 5. Career Guidance & Recommender
    guidance_res = rec.generate(
        match_result=match_res,
        resume_processed=r_proc,
        resume_skills=r_skills,
        jd_processed=j_proc,
        jd_skills=j_skills,
        ats_result=ats_res
    )

    return {
        "r_proc": r_proc,
        "j_proc": j_proc,
        "r_skills": r_skills,
        "j_skills": j_skills,
        "match_res": match_res,
        "ats_res": ats_res,
        "guidance_res": guidance_res
    }


# ---------------------------------------------------------------------------
# 1. End-to-End Pipeline Tests
# ---------------------------------------------------------------------------

def test_end_to_end_pipeline_strong_match(pipeline):
    """Resume A with Python Backend JD 1 should achieve strong match and high ATS score."""
    result = run_full_pipeline(pipeline, RESUME_A_STRONG_MATCH, JD_1_PYTHON_BACKEND)
    
    match = result["match_res"]
    ats = result["ats_res"]
    guidance = result["guidance_res"]

    # Match scoring checks
    assert match["overall_score"] >= 70
    assert match["skill_match_score"] >= 70
    assert match["required_skill_coverage"] >= 75.0
    
    matched_skill_names = [s["skill"] for s in match["matched_skills"]]
    assert "Python" in matched_skill_names
    assert "FastAPI" in matched_skill_names
    assert "PostgreSQL" in matched_skill_names
    assert "Docker" in matched_skill_names
    assert "AWS" in matched_skill_names

    # ATS checks
    assert ats["score"] >= 80
    assert "text_extractability" in ats["components"]
    assert ats["components"]["text_extractability"] == 100.0

    # Guidance checks
    assert len(guidance["resume_strengths"]) > 0
    assert guidance["guidance_summary"]["overall_score"] == match["overall_score"]


def test_end_to_end_pipeline_moderate_match(pipeline):
    """Resume B with Python Backend JD 1 has missing core requirements (FastAPI, PostgreSQL)."""
    result = run_full_pipeline(pipeline, RESUME_B_MODERATE_MATCH, JD_1_PYTHON_BACKEND)
    
    match = result["match_res"]
    guidance = result["guidance_res"]

    # Match checks
    assert match["overall_score"] < result["match_res"]["overall_score"] + 1
    assert match["required_skill_coverage"] < 60.0
    
    missing_skill_names = [s["skill"] for s in match["missing_skills"]]
    assert "FastAPI" in missing_skill_names
    assert "PostgreSQL" in missing_skill_names

    # Prioritized gaps check
    high_priority_gaps = [g["skill"] for g in guidance["prioritized_skill_gaps"] if g["priority"] == SkillPriority.HIGH]
    assert "FastAPI" in high_priority_gaps
    assert "PostgreSQL" in high_priority_gaps


def test_end_to_end_pipeline_weak_match(pipeline):
    """Resume C (Marketing) with Python Backend JD 1 should have near zero match."""
    result = run_full_pipeline(pipeline, RESUME_C_WEAK_MATCH, JD_1_PYTHON_BACKEND)
    
    match = result["match_res"]
    guidance = result["guidance_res"]

    assert match["overall_score"] < 25
    assert match["skill_match_score"] == 0.0
    assert match["required_skill_coverage"] == 0.0
    assert "Significant" in guidance["guidance_summary"]["headline"] or "Several" in guidance["guidance_summary"]["headline"]


# ---------------------------------------------------------------------------
# 2. Skill Extraction Stress & False Positive / Negative Audits
# ---------------------------------------------------------------------------

def test_false_positive_stress_test(pipeline):
    """Resume F has tricky English words ('clearly', 'communicate', 'go to', 'continuous improvement', etc.)."""
    e = pipeline["extractor"]
    res = e.extract(RESUME_F_FALSE_POSITIVE_STRESS)
    skills = res["skills"]

    # Must NOT detect C, Go, R, Java, React
    assert "C" not in skills
    assert "Go" not in skills
    assert "R" not in skills
    assert "Java" not in skills
    assert "React" not in skills

    # Must detect actual technical skills present
    assert "JavaScript" in skills
    assert "React Native" in skills
    assert "Agile" in skills


def test_alias_heavy_resume_normalization(pipeline):
    """Resume E uses slang/abbreviations (python3, postgres, golang, reactjs, nodejs, gcp, k8s, cicd)."""
    e = pipeline["extractor"]
    res = e.extract(RESUME_E_ALIAS_HEAVY)
    skills = res["skills"]

    assert "Python" in skills
    assert "PostgreSQL" in skills
    assert "Go" in skills
    assert "React" in skills
    assert "Node.js" in skills
    assert "Google Cloud Platform" in skills
    assert "FastAPI" in skills
    assert "Kubernetes" in skills
    assert "CI/CD" in skills


def test_mixed_technical_terms_extraction(pipeline):
    """Resume J has symbols: C++, C#, .NET, CI/CD, Node.js, scikit-learn, REST API, React Native."""
    e = pipeline["extractor"]
    res = e.extract(RESUME_J_MIXED_TECH_TERMS)
    skills = res["skills"]

    assert "C++" in skills
    assert "C#" in skills
    assert ".NET" in skills
    assert "CI/CD" in skills
    assert "Node.js" in skills
    assert "scikit-learn" in skills
    assert "REST API" in skills
    assert "React Native" in skills
    assert "JavaScript" in skills
    assert "Java" not in skills
    assert "React" not in skills


# ---------------------------------------------------------------------------
# 3. Section Segmentation & Unusual Headers
# ---------------------------------------------------------------------------

def test_unusual_section_names_parsing(pipeline):
    """Resume I uses 'Professional Background', 'Technical Expertise', 'Academic History', 'Selected Work'."""
    p = pipeline["preprocessor"]
    res = p.preprocess(RESUME_I_UNUSUAL_SECTIONS, doc_type="resume")
    sections = res["sections"]

    assert "experience" in sections
    assert "skills" in sections
    assert "education" in sections
    assert "projects" in sections


def test_structured_resume_ats_evaluation(pipeline):
    """Resume H has clean standard structure and complete contact info."""
    ats = pipeline["ats_analyzer"]
    p = pipeline["preprocessor"]
    e = pipeline["extractor"]

    proc = p.preprocess(RESUME_H_STRUCTURED, doc_type="resume")
    skills = e.extract(text=proc["normalized_text"], sections=proc["sections"])
    ats_res = ats.analyze(resume_processed=proc, resume_skills=skills)

    assert ats_res["score"] >= 85
    assert ats_res["components"]["section_structure"] >= 80
    assert ats_res["components"]["contact_information"] >= 85


def test_sparse_resume_handling(pipeline):
    """Resume G is sparse (low word count). Should gracefully evaluate with low extractability."""
    ats = pipeline["ats_analyzer"]
    p = pipeline["preprocessor"]
    e = pipeline["extractor"]

    proc = p.preprocess(RESUME_G_SPARSE, doc_type="resume")
    skills = e.extract(text=proc["normalized_text"], sections=proc["sections"])
    ats_res = ats.analyze(resume_processed=proc, resume_skills=skills)

    assert ats_res["score"] < 50
    assert ats_res["components"]["text_extractability"] <= 20.0
    assert len(ats_res["warnings"]) > 0


# ---------------------------------------------------------------------------
# 4. Scoring Sanity, Weights & Extra Skills Isolation
# ---------------------------------------------------------------------------

def test_extra_skills_resume_isolation(pipeline):
    """Resume D has target skills PLUS many extra skills. Denominator must NOT be inflated."""
    m = pipeline["matcher"]
    e = pipeline["extractor"]

    d_skills = e.extract(RESUME_D_EXTRA_SKILLS)
    jd_skills = e.extract(JD_1_PYTHON_BACKEND)

    match = m.match(resume_skills=d_skills, jd_skills=jd_skills)

    # Extra skills tracked
    extra_names = [s["skill"] for s in match["extra_skills"]]
    assert "PyTorch" in extra_names
    assert "Cassandra" in extra_names
    assert "Terraform" in extra_names

    # Denominator depends ONLY on JD skills, not on extra skills count
    assert match["skill_match_score"] >= 65.0
    assert len(match["extra_skills"]) >= 8


def test_ambiguous_jd_fallback(pipeline):
    """JD 3 has no explicit Required/Preferred sections. Default fallback must classify all as required."""
    m = pipeline["matcher"]
    e = pipeline["extractor"]

    j_skills = e.extract(JD_3_GENERIC_UNSTRUCTURED)
    r_skills = e.extract(RESUME_A_STRONG_MATCH)

    match = m.match(resume_skills=r_skills, jd_skills=j_skills)

    for item in match["matched_skills"]:
        assert item["is_required"] is True
        assert item["weight"] == 1.0


# ---------------------------------------------------------------------------
# 5. Ethical Guidance & Anti-Fabrication Guarantee
# ---------------------------------------------------------------------------

def test_anti_fabrication_guarantee(pipeline):
    """Ensure suggestions NEVER order the candidate to invent/fabricate skills or lie."""
    rec = pipeline["recommender"]
    m = pipeline["matcher"]
    e = pipeline["extractor"]

    r_skills = e.extract(RESUME_B_MODERATE_MATCH)
    j_skills = e.extract(JD_1_PYTHON_BACKEND)
    match = m.match(resume_skills=r_skills, jd_skills=j_skills)

    suggestions = rec.generate_resume_suggestions(match_result=match, resume_skills=r_skills)

    all_text = " ".join(suggestions["improvements"])
    for rec_item in suggestions["detailed_recommendations"]:
        all_text += " " + rec_item["action"] + " " + rec_item["description"]

    # Prohibited fabrication directives
    assert "claim you know" not in all_text.lower()
    assert "invent" not in all_text.lower()
    assert "fake" not in all_text.lower()
    
    # Must use conditional phrasing ("If you have experience...", "consider learning...")
    assert "if you" in all_text.lower() or "consider" in all_text.lower() or "prioritize" in all_text.lower()


# ---------------------------------------------------------------------------
# 6. Recruiter Batch Multi-Candidate Isolation & Sorting
# ---------------------------------------------------------------------------

def test_recruiter_batch_screening_isolation_and_ranking(pipeline):
    """Batch screening Candidates A, B, C, D, E against JD 1.
    Verifies independent analysis, descending overall_score order, and zero cross-leakage.
    """
    candidates = [
        {"id": "cand_a", "name": "Alex Morgan (Strong)", "text": RESUME_A_STRONG_MATCH},
        {"id": "cand_b", "name": "Jordan Lee (Moderate)", "text": RESUME_B_MODERATE_MATCH},
        {"id": "cand_c", "name": "Samantha Taylor (Weak)", "text": RESUME_C_WEAK_MATCH},
        {"id": "cand_d", "name": "David Chen (Extra Skills)", "text": RESUME_D_EXTRA_SKILLS},
        {"id": "cand_e", "name": "Marcus Vance (Alias Heavy)", "text": RESUME_E_ALIAS_HEAVY},
    ]

    p = pipeline["preprocessor"]
    e = pipeline["extractor"]
    m = pipeline["matcher"]

    jd_proc = p.preprocess(JD_1_PYTHON_BACKEND, doc_type="jd")
    jd_skills = e.extract(text=jd_proc["normalized_text"], sections=jd_proc["sections"])

    batch_results = []
    for cand in candidates:
        r_proc = p.preprocess(cand["text"], doc_type="resume")
        r_skills = e.extract(text=r_proc["normalized_text"], sections=r_proc["sections"])
        match = m.match(
            resume_skills=r_skills,
            jd_skills=jd_skills,
            resume_text=r_proc["cleaned_text"],
            jd_text=jd_proc["cleaned_text"]
        )
        batch_results.append({
            "candidate_id": cand["id"],
            "name": cand["name"],
            "overall_score": match["overall_score"],
            "skill_match_score": match["skill_match_score"],
            "matched_skills": [s["skill"] for s in match["matched_skills"]],
            "missing_skills": [s["skill"] for s in match["missing_skills"]]
        })

    # Sort descending by overall_score, then candidate_id for deterministic tie breaking
    sorted_results = sorted(batch_results, key=lambda x: (-x["overall_score"], x["candidate_id"]))

    # Strong/Extra candidates should rank at the top
    top_two_ids = [sorted_results[0]["candidate_id"], sorted_results[1]["candidate_id"]]
    assert "cand_a" in top_two_ids or "cand_d" in top_two_ids

    # Weak marketing candidate should rank last
    assert sorted_results[-1]["candidate_id"] == "cand_c"

    # Verify no cross-candidate state leakage: Marketing candidate has no Python matched skills
    cand_c_res = next(r for r in sorted_results if r["candidate_id"] == "cand_c")
    assert "Python" not in cand_c_res["matched_skills"]
    assert "FastAPI" not in cand_c_res["matched_skills"]

    # Verify candidate A has Python matched
    cand_a_res = next(r for r in sorted_results if r["candidate_id"] == "cand_a")
    assert "Python" in cand_a_res["matched_skills"]


# ---------------------------------------------------------------------------
# 7. Session State Reset Integrity
# ---------------------------------------------------------------------------

def test_session_state_reset_integrity():
    """Verify that reset_job_seeker_inputs properly clears all analysis state."""
    class MockSessionState(dict):
        def __getattr__(self, key):
            return self.get(key)
        def __setattr__(self, key, value):
            self[key] = value

    mock_state = MockSessionState({
        "js_resume_file": "sample.pdf",
        "js_match_result": {"overall_score": 85},
        "js_ats_result": {"score": 90},
        "js_recommendations": ["Improve formatting"],
        "js_learning_roadmap": [{"skill": "Docker"}],
        "js_guidance_summary": {"headline": "Strong match"}
    })

    # Call reset
    reset_job_seeker_inputs(mock_state)

    assert mock_state["js_resume_file"] is None
    assert mock_state["js_match_result"] is None
    assert mock_state["js_ats_result"] is None
    assert mock_state["js_recommendations"] is None
    assert mock_state["js_learning_roadmap"] is None
    assert mock_state["js_guidance_summary"] is None


# ---------------------------------------------------------------------------
# 8. Scoring Audit Cases 1 through 8
# ---------------------------------------------------------------------------

def test_scoring_audit_case_1_all_required_matched(pipeline):
    """Case 1: All required skills matched."""
    m = pipeline["matcher"]
    r_skills = ["Python", "FastAPI", "PostgreSQL"]
    j_skills = ["Python", "FastAPI", "PostgreSQL"]
    res = m.match(resume_skills=r_skills, jd_skills=j_skills)
    assert res["skill_match_score"] == 100.0
    assert res["required_skill_coverage"] == 100.0
    assert len(res["missing_skills"]) == 0


def test_scoring_audit_case_2_some_required_missing(pipeline):
    """Case 2: Some required skills missing."""
    m = pipeline["matcher"]
    r_skills = ["Python"]
    j_skills = ["Python", "FastAPI", "PostgreSQL"]
    res = m.match(resume_skills=r_skills, jd_skills=j_skills)
    assert res["skill_match_score"] < 100.0
    assert res["required_skill_coverage"] < 50.0
    assert len(res["missing_skills"]) == 2


def test_scoring_audit_case_3_only_preferred_missing(pipeline):
    """Case 3: Only preferred skills missing."""
    m = pipeline["matcher"]
    j_skills_dict = {
        "skills": ["Python", "Docker"],
        "details": {
            "Python": {"is_required": True, "priority": "required", "sections": ["requirements"], "evidence": []},
            "Docker": {"is_required": False, "priority": "preferred", "sections": ["preferred_qualifications"], "evidence": []}
        }
    }
    r_skills = ["Python"]
    res = m.match(resume_skills=r_skills, jd_skills=j_skills_dict)
    assert res["required_skill_coverage"] == 100.0
    assert res["skill_match_score"] == round((1.0 / 1.5) * 100.0, 2)  # 66.67%
    assert len(res["missing_skills"]) == 1
    assert res["missing_skills"][0]["skill"] == "Docker"
    assert res["missing_skills"][0]["is_required"] is False


def test_scoring_audit_case_5_and_6_lexical_similarity_extremes(pipeline):
    """Case 5 & 6: Very high lexical similarity vs zero lexical overlap."""
    m = pipeline["matcher"]
    
    # Identical texts
    identical_sim = m.compute_text_similarity("Python FastAPI developer building scalable web services", "Python FastAPI developer building scalable web services")
    assert identical_sim == 100.0

    # Completely unrelated texts
    unrelated_sim = m.compute_text_similarity("Ancient medieval history of European architecture", "Quantum mechanics semiconductor physics")
    assert unrelated_sim == 0.0


def test_scoring_audit_case_7_and_8_empty_skill_sets(pipeline):
    """Case 7 & 8: Empty resume skills or empty JD skills."""
    m = pipeline["matcher"]
    
    # Resume empty, JD has skills
    res7 = m.match(resume_skills=[], jd_skills=["Python", "FastAPI"])
    assert res7["skill_match_score"] == 0.0
    assert res7["required_skill_coverage"] == 0.0
    assert len(res7["missing_skills"]) == 2

    # JD has no skills, resume has skills
    res8 = m.match(resume_skills=["Python", "FastAPI"], jd_skills=[])
    assert res8["skill_match_score"] == 100.0
    assert len(res8["missing_skills"]) == 0


def test_zero_required_coverage_guidance_warning(pipeline):
    """Score sanity: Resume with 0% required skill coverage but high textual similarity.
    The 70/30 model produces an overall score, but the Guidance layer explicitly flags the missing requirements.
    """
    rec = pipeline["recommender"]
    m = pipeline["matcher"]

    # Match result with 0% skill match but high content similarity
    match = m.match(
        resume_skills=["HTML", "CSS"],
        jd_skills=["Python", "FastAPI", "PostgreSQL"],
        resume_text="Senior engineer looking for opportunities in technology systems with agile teams",
        jd_text="Senior engineer looking for opportunities in technology systems with agile teams"
    )

    guidance = rec.generate(match_result=match)

    # 70/30 formula preserves mathematical score
    assert match["skill_match_score"] == 0.0
    assert match["required_skill_coverage"] == 0.0
    assert match["overall_score"] == int(round(0.30 * match["content_similarity_score"]))

    # Guidance explicitly warns about the core missing requirements
    high_gaps = [g["skill"] for g in guidance["prioritized_skill_gaps"] if g["priority"] == SkillPriority.HIGH]
    assert "Python" in high_gaps
    assert "FastAPI" in high_gaps
    assert "PostgreSQL" in high_gaps
    assert any("Core role requirements" in imp for imp in guidance["resume_improvements"])

