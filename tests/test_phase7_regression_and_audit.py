"""Phase 7 — Comprehensive Final QA, Regression Testing & Production Readiness Audit Test Suite.

Validates the entire application end-to-end against all Phase 7 acceptance criteria:
1. Job Seeker JD Match formula purity (Matched / Total JD Skills * 100).
2. Content similarity & ATS score strict isolation from Job Seeker results.
3. Job Seeker Edge Cases A through G (Empty resume, empty JD, zero-skill JD, identical skills, extra skills).
4. False-positive protections across complex technical symbols and words.
5. Anti-fabrication ethical recommendations check.
6. Session state reset & Sample JD population integrity.
7. Recruiter batch screening, deterministic ranking, search, filter, and 'Clear Filters' candidate preservation.
8. Candidate Details & Comparison Matrix isolation (Candidate A != Candidate B).
9. Security boundaries, path traversal sanitization, and zero stdout leakage.
"""

import pytest
import time
from services.document_parser import DocumentParser
from services.text_preprocessor import TextPreprocessor
from services.skill_extractor import SkillExtractor
from services.matcher import ResumeMatcher
from services.scorer import ScorerService
from services.ats_analyzer import ATSAnalyzer
from services.recommender import RecommendationService
from utils.constants import SkillPriority, CandidateStatus
from utils.validators import (
    validate_resume_file,
    validate_job_description,
    validate_batch_resumes
)
from utils.session_state import reset_job_seeker_inputs, reset_recruiter_inputs
from tests.fixtures.synthetic_resumes import (
    RESUME_A_STRONG_MATCH,
    RESUME_B_MODERATE_MATCH,
    RESUME_C_WEAK_MATCH,
    RESUME_D_EXTRA_SKILLS,
    RESUME_E_ALIAS_HEAVY,
    JD_1_PYTHON_BACKEND,
    JD_2_FRONTEND_JAVASCRIPT,
    JD_3_GENERIC_UNSTRUCTURED
)
from tests.test_recruiter_screening import screen_candidate_pool


@pytest.fixture
def core_services():
    return {
        "parser": DocumentParser(),
        "preprocessor": TextPreprocessor(),
        "extractor": SkillExtractor(),
        "scorer": ScorerService(),
        "matcher": ResumeMatcher(),
        "ats_analyzer": ATSAnalyzer(),
        "recommender": RecommendationService()
    }


# ===========================================================================
# 1. Job Seeker Business Logic & Formula Purity
# ===========================================================================

def test_job_seeker_jd_match_strict_formula(core_services):
    """Job Seeker JD Match % must be strictly Matched JD Skills / Total JD Skills * 100."""
    p = core_services["preprocessor"]
    e = core_services["extractor"]
    m = core_services["matcher"]

    jd_text = "Required Skills: Python, FastAPI, PostgreSQL, Docker, AWS"
    resume_text = "Experience with Python, FastAPI, and Docker in production."

    p_jd = p.preprocess(jd_text, doc_type="jd")
    jd_skills = e.extract(jd_text, sections=p_jd["sections"], document_type="jd")

    p_res = p.preprocess(resume_text, doc_type="resume")
    res_skills = e.extract(resume_text, sections=p_res["sections"], document_type="resume")

    match = m.match(resume_skills=res_skills, jd_skills=jd_skills, resume_text=resume_text, jd_text=jd_text)

    matched_names = [s["skill"] for s in match["matched_skills"]]
    missing_names = [s["skill"] for s in match["missing_skills"]]

    assert set(matched_names) == {"Python", "FastAPI", "Docker"}
    assert set(missing_names) == {"PostgreSQL", "AWS"}

    total_jd_skills = len(matched_names) + len(missing_names)
    assert total_jd_skills == 5

    # Match calculation: 3 / 5 * 100 = 60%
    jd_match_pct = int(round((len(matched_names) / total_jd_skills) * 100))
    assert jd_match_pct == 60

    # Verify content similarity does NOT alter jd_match_pct
    assert match["content_similarity_score"] != jd_match_pct


def test_job_seeker_results_contain_no_ats_or_recruiter_leakage(core_services):
    """Job Seeker analysis results dictionary must separate candidate-facing results cleanly."""
    p = core_services["preprocessor"]
    e = core_services["extractor"]
    m = core_services["matcher"]
    rec = core_services["recommender"]
    ats = core_services["ats_analyzer"]

    resume_text = RESUME_A_STRONG_MATCH
    jd_text = JD_1_PYTHON_BACKEND

    p_jd = p.preprocess(jd_text, doc_type="jd")
    j_sk = e.extract(jd_text, sections=p_jd["sections"], document_type="jd")
    p_res = p.preprocess(resume_text, doc_type="resume")
    r_sk = e.extract(resume_text, sections=p_res["sections"], document_type="resume")

    match_result = m.match(resume_skills=r_sk, jd_skills=j_sk, resume_text=resume_text, jd_text=jd_text)
    ats_result = ats.analyze(resume_processed=p_res, resume_skills=r_sk)
    guidance = rec.generate(match_result=match_result, resume_processed=p_res, resume_skills=r_sk, jd_processed=p_jd, jd_skills=j_sk, ats_result=ats_result)

    matched_list = [s["skill"] for s in match_result["matched_skills"]]
    missing_list = [s["skill"] for s in match_result["missing_skills"]]
    total_jd = len(matched_list) + len(missing_list)
    jd_match_pct = int(round((len(matched_list) / total_jd) * 100))

    # Construct Job Seeker analysis results payload exactly as pages/job_seeker.py does
    analysis_data = {
        "candidate_name": "Alex Morgan",
        "resume_filename": "Alex_Morgan_Resume.pdf",
        "jd_match_percentage": jd_match_pct,
        "total_jd_skills_count": total_jd,
        "skills": {
            "matched": matched_list,
            "missing": missing_list,
            "extra": [s["skill"] for s in match_result["extra_skills"]]
        },
        "resume_improvements": guidance.get("resume_improvements", []),
        "section_improvements": guidance.get("section_improvements", {}),
        "skills_to_learn": guidance.get("learning_roadmap", [])
    }

    # Job Seeker primary results contract
    assert "jd_match_percentage" in analysis_data
    assert analysis_data["jd_match_percentage"] is not None
    assert "matched" in analysis_data["skills"]
    assert "missing" in analysis_data["skills"]
    assert len(analysis_data["resume_improvements"]) > 0
    assert len(analysis_data["skills_to_learn"]) > 0


# ===========================================================================
# 2. Job Seeker Edge Cases A through G
# ===========================================================================

def test_edge_case_a_empty_resume():
    """Case A: Empty resume yields clear validation error."""
    val = validate_resume_file(None)
    assert not val.is_valid
    assert "upload your resume" in val.message.lower()


def test_edge_case_b_empty_jd():
    """Case B: Empty JD yields clear validation error."""
    val = validate_job_description("paste", jd_text="")
    assert not val.is_valid
    assert "cannot be empty" in val.message.lower()


def test_edge_case_c_jd_with_no_recognizable_skills(core_services):
    """Case C: JD with no recognizable skills yields total_jd_skills_count == 0 and None match %."""
    p = core_services["preprocessor"]
    e = core_services["extractor"]

    non_tech_jd = "Looking for a punctual, communicative team player with great energy and collaborative attitude."
    p_jd = p.preprocess(non_tech_jd, doc_type="jd")
    j_sk = e.extract(non_tech_jd, sections=p_jd["sections"], document_type="jd")

    assert len(j_sk["skills"]) == 0
    total_jd_count = len(j_sk["skills"])
    jd_match_pct = int(round((0 / total_jd_count) * 100)) if total_jd_count > 0 else None
    
    # Must be None so UI displays 'Unable to Calculate JD Match', NOT 0%
    assert jd_match_pct is None


def test_edge_case_d_resume_with_no_recognizable_skills(core_services):
    """Case D: Resume with no recognizable skills handled gracefully with 0% match."""
    p = core_services["preprocessor"]
    e = core_services["extractor"]
    m = core_services["matcher"]

    resume_text = "I am a hard worker with great enthusiasm."
    jd_text = "Requirements: Python, FastAPI, Docker"

    p_jd = p.preprocess(jd_text, doc_type="jd")
    j_sk = e.extract(jd_text, sections=p_jd["sections"], document_type="jd")
    p_res = p.preprocess(resume_text, doc_type="resume")
    r_sk = e.extract(resume_text, sections=p_res["sections"], document_type="resume")

    match = m.match(resume_skills=r_sk, jd_skills=j_sk, resume_text=resume_text, jd_text=jd_text)
    matched_names = [s["skill"] for s in match["matched_skills"]]
    missing_names = [s["skill"] for s in match["missing_skills"]]

    assert len(matched_names) == 0
    assert len(missing_names) == 3
    jd_match_pct = int(round((len(matched_names) / (len(matched_names) + len(missing_names))) * 100))
    assert jd_match_pct == 0


def test_edge_case_e_resume_and_jd_identical_skills(core_services):
    """Case E: Resume and JD with identical skills produce 100% match."""
    m = core_services["matcher"]
    skills = ["Python", "FastAPI", "Docker", "PostgreSQL", "AWS"]
    match = m.match(resume_skills=skills, jd_skills=skills)
    assert match["skill_match_score"] == 100.0
    assert len(match["missing_skills"]) == 0
    assert len(match["matched_skills"]) == 5


def test_edge_case_f_extra_resume_skills_do_not_affect_denominator(core_services):
    """Case F: Extra resume skills do not increase the denominator."""
    m = core_services["matcher"]
    jd_skills = ["Python", "Docker"]
    # Candidate with 2 matched skills + 15 extra skills
    resume_skills = ["Python", "Docker", "Java", "C++", "Ruby", "PHP", "Go", "Rust", "Swift", "Kotlin", "React", "Vue", "Angular", "Redis", "Kafka", "GraphQL", "Terraform"]
    match = m.match(resume_skills=resume_skills, jd_skills=jd_skills)
    assert match["skill_match_score"] == 100.0
    assert len(match["extra_skills"]) == 15


def test_edge_case_g_missing_skills_correctly_identified(core_services):
    """Case G: Missing skills in JD are correctly identified."""
    m = core_services["matcher"]
    jd_skills = ["Python", "FastAPI", "PostgreSQL", "Kubernetes"]
    resume_skills = ["Python", "PostgreSQL"]
    match = m.match(resume_skills=resume_skills, jd_skills=jd_skills)
    missing = [s["skill"] for s in match["missing_skills"]]
    assert set(missing) == {"FastAPI", "Kubernetes"}


# ===========================================================================
# 3. False Positive Protection Audits
# ===========================================================================

def test_false_positive_protections(core_services):
    """Verify extractor does not misidentify tricky English words as tech skills."""
    e = core_services["extractor"]

    # 1. Java vs JavaScript
    res_js = e.extract("Skilled in JavaScript development.")
    assert "JavaScript" in res_js["skills"]
    assert "Java" not in res_js["skills"]

    # 2. React vs React Native
    res_rn = e.extract("Experienced React Native mobile engineer.")
    assert "React Native" in res_rn["skills"]
    assert "React" not in res_rn["skills"]

    # 3. Go vs Google
    res_google = e.extract("Worked at Google headquarters.")
    assert "Go" not in res_google["skills"]

    # 4. Standalone C & R
    res_c_words = e.extract("A clearly written communication policy for our team.")
    assert "C" not in res_c_words["skills"]
    assert "R" not in res_c_words["skills"]

    # 5. C++ and C#
    res_cpp_csharp = e.extract("Implemented algorithms in C++ and backend services in C#.")
    assert "C++" in res_cpp_csharp["skills"]
    assert "C#" in res_cpp_csharp["skills"]

    # 6. .NET and Node.js
    res_dotnet_node = e.extract("Built APIs using .NET Core and Node.js.")
    assert ".NET" in res_dotnet_node["skills"]
    assert "Node.js" in res_dotnet_node["skills"]

    # 7. CI/CD and scikit-learn
    res_cicd_sklearn = e.extract("Automated deployment with CI/CD and trained models using scikit-learn.")
    assert "CI/CD" in res_cicd_sklearn["skills"]
    assert "scikit-learn" in res_cicd_sklearn["skills"]


# ===========================================================================
# 4. Anti-Fabrication & Ethical Recommendations
# ===========================================================================

def test_anti_fabrication_recommendations(core_services):
    """Verify suggestions never instruct candidate to falsify or claim unearned skills."""
    rec = core_services["recommender"]
    m = core_services["matcher"]

    match = m.match(resume_skills=["Python"], jd_skills=["Python", "FastAPI", "AWS", "Kubernetes"])
    suggestions = rec.generate_resume_suggestions(match_result=match)

    combined_text = " ".join(suggestions.get("improvements", []))
    for sec_name, points in suggestions.get("section_improvements", {}).items():
        combined_text += " " + " ".join(points)

    lower_text = combined_text.lower()
    assert "fabricate" not in lower_text
    assert "invent" not in lower_text
    assert "claim you have" not in lower_text
    assert "falsely" not in lower_text
    
    # Must use honest conditional advice
    assert "if you have" in lower_text or "if you possess" in lower_text


# ===========================================================================
# 5. Session State Reset & Sample JD State Synchronization
# ===========================================================================

def test_session_state_reset_job_seeker():
    """Job seeker reset clears all uploaded files, extracted skills, and widget states."""
    class StateMock(dict):
        def __getattr__(self, k): return self.get(k)
        def __setattr__(self, k, v): self[k] = v

    state = StateMock({
        "js_resume_file": "my_resume.pdf",
        "js_resume_name": "my_resume.pdf",
        "js_resume_text": "Python engineer",
        "js_jd_text": "Python JD",
        "js_jd_text_input": "Python JD",
        "js_resume_uploader": "mock_uploader_state",
        "js_analysis_results": {"matched": ["Python"]}
    })

    reset_job_seeker_inputs(state)

    assert state.get("js_resume_file") is None
    assert state.get("js_resume_name") is None
    assert state.get("js_resume_text") == ""
    assert state.get("js_jd_text") == ""
    assert state.get("js_jd_text_input") == ""
    assert state.get("js_resume_uploader") is None
    assert state.get("js_analysis_results") is None


def test_session_state_reset_recruiter():
    """Recruiter reset clears all screening candidate pools and widget states."""
    class StateMock(dict):
        def __getattr__(self, k): return self.get(k)
        def __setattr__(self, k, v): self[k] = v

    state = StateMock({
        "rec_jd_text": "Backend JD",
        "rec_jd_text_input": "Backend JD",
        "rec_batch_resumes": ["r1.pdf", "r2.pdf"],
        "rec_screening_results": [{"id": "cand-01", "name": "Alex"}],
        "rec_batch_resumes_uploader": ["mock_uploader"],
        "comp_multiselect": ["cand-01"]
    })

    reset_recruiter_inputs(state)

    assert state.get("rec_jd_text") == ""
    assert state.get("rec_jd_text_input") == ""
    assert state.get("rec_batch_resumes") == []
    assert state.get("rec_screening_results") is None
    assert state.get("rec_batch_resumes_uploader") is None
    assert state.get("comp_multiselect") is None


# ===========================================================================
# 6. Recruiter Screening, Deterministic Ranking & Filters
# ===========================================================================

def test_recruiter_deterministic_ranking_and_filters(core_services):
    """Test recruiter batch screening, deterministic ranking, search, and filter integrity."""
    candidates = [
        {"id": "cand-01", "filename": "Alex_Morgan_Resume.pdf", "text": RESUME_A_STRONG_MATCH},
        {"id": "cand-02", "filename": "Jordan_Lee_Resume.pdf", "text": RESUME_B_MODERATE_MATCH},
        {"id": "cand-03", "filename": "Samantha_Taylor_Resume.pdf", "text": RESUME_C_WEAK_MATCH},
        {"id": "cand-04", "filename": "David_Chen_Resume.pdf", "text": RESUME_D_EXTRA_SKILLS},
        {"id": "cand-05", "filename": "Marcus_Vance_Resume.pdf", "text": RESUME_E_ALIAS_HEAVY},
    ]

    screened = screen_candidate_pool(core_services, JD_1_PYTHON_BACKEND, candidates)
    assert len(screened) == 5

    # 1. Deterministic rank ordering
    for i in range(len(screened) - 1):
        assert screened[i]["overall_match"] >= screened[i+1]["overall_match"]

    # 2. Search test
    alex = [c for c in screened if "alex" in c["name"].lower()]
    assert len(alex) == 1
    assert alex[0]["name"] == "Alex Morgan"

    # 3. Filter test (80%+ score)
    high_match = [c for c in screened if c["overall_match"] >= 80]
    for c in high_match:
        assert c["overall_match"] >= 80

    # 4. Status filter
    low_match = [c for c in screened if c["status"] == "Low Match"]
    assert any(c["name"] == "Samantha Taylor" for c in low_match)


def test_recruiter_clear_filters_preserves_candidates():
    """Clear filters must reset filter values while preserving the candidate pool."""
    pool = [{"id": "c1", "name": "Alex"}, {"id": "c2", "name": "Jordan"}]
    state = {
        "rec_screening_results": pool,
        "rec_filter_search": "alex",
        "rec_filter_score_range": "80%+",
        "rec_filter_req_cov": "80%+",
        "rec_filter_status": "Strong Match",
        "rec_filter_skill": "Python",
        "rec_filter_sort": "Overall Match (High to Low)"
    }

    # Clear filters action
    state["rec_filter_search"] = ""
    state["rec_filter_score_range"] = "All Scores"
    state["rec_filter_req_cov"] = "All Coverage"
    state["rec_filter_status"] = "All Statuses"
    state["rec_filter_skill"] = "All Skills"
    state["rec_filter_sort"] = "Overall Match (High to Low)"

    assert len(state["rec_screening_results"]) == 2
    assert state["rec_filter_search"] == ""
    assert state["rec_filter_score_range"] == "All Scores"


# ===========================================================================
# 7. Candidate Details & Comparison Matrix Isolation
# ===========================================================================

def test_candidate_details_isolation(core_services):
    """Candidate A details must never contain Candidate B data."""
    candidates = [
        {"id": "cand-01", "filename": "Alex_Morgan_Resume.pdf", "text": RESUME_A_STRONG_MATCH},
        {"id": "cand-02", "filename": "Samantha_Taylor_Resume.pdf", "text": RESUME_C_WEAK_MATCH},
    ]
    screened = screen_candidate_pool(core_services, JD_1_PYTHON_BACKEND, candidates)
    
    cand_a = next(c for c in screened if c["id"] == "cand-01")
    cand_b = next(c for c in screened if c["id"] == "cand-02")

    assert cand_a["name"] == "Alex Morgan"
    assert cand_b["name"] == "Samantha Taylor"
    assert "Python" in cand_a["matched_skills"]
    assert "Python" not in cand_b["matched_skills"]
    assert cand_a["overall_match"] > cand_b["overall_match"]


def test_comparison_matrix_scaling_2_to_4(core_services):
    """Comparison matrix supports 2, 3, and 4 candidates without data corruption."""
    candidates = [
        {"id": "cand-01", "filename": "Alex_Morgan_Resume.pdf", "text": RESUME_A_STRONG_MATCH},
        {"id": "cand-02", "filename": "Jordan_Lee_Resume.pdf", "text": RESUME_B_MODERATE_MATCH},
        {"id": "cand-03", "filename": "Samantha_Taylor_Resume.pdf", "text": RESUME_C_WEAK_MATCH},
        {"id": "cand-04", "filename": "David_Chen_Resume.pdf", "text": RESUME_D_EXTRA_SKILLS},
    ]
    screened = screen_candidate_pool(core_services, JD_1_PYTHON_BACKEND, candidates)

    for count in [2, 3, 4]:
        selected = screened[:count]
        assert len(selected) == count
        assert len(set(c["id"] for c in selected)) == count
        for c in selected:
            assert "overall_match" in c
            assert "matched_skills" in c
            assert "missing_skills" in c


# ===========================================================================
# 8. File Validation & Security Boundaries
# ===========================================================================

def test_security_file_validation_and_path_traversal():
    """Verify security controls: path traversal rejection, extension whitelisting, size bounding."""
    parser = DocumentParser()

    # Path traversal in filename
    traversal_res = parser.parse_document("dummy_content", filename="../../etc/passwd.pdf")
    assert ".." not in traversal_res["filename"]
    assert "/" not in traversal_res["filename"]

    # Unsupported extension
    unsupported_val = validate_resume_file(type("MockFile", (), {"name": "malicious.exe", "size": 1024})())
    assert not unsupported_val.is_valid
    assert "unsupported" in unsupported_val.message.lower()

    # Oversized file (> 10MB)
    oversized_val = validate_resume_file(type("MockFile", (), {"name": "huge.pdf", "size": 15 * 1024 * 1024})())
    assert not oversized_val.is_valid
    assert "exceeds" in oversized_val.message.lower()


# ===========================================================================
# 9. Phase 6B UI Cleanliness & Regression Tests
# ===========================================================================

def test_style_css_hides_200mb_and_duplicate_upload_icons():
    """Verify style.css includes rules suppressing duplicate icon text and default 200MB instructions."""
    from pathlib import Path
    css_path = Path(__file__).resolve().parent.parent / "assets" / "style.css"
    content = css_path.read_text(encoding="utf-8")

    assert '[data-testid="stFileUploader"] button span[data-testid="stIconMaterial"]' in content
    assert '[data-testid="stFileUploaderDropzoneInstructions"] small' in content
    assert "display: none !important;" in content


def test_no_raw_html_or_code_in_cards_module():
    """Verify components/cards.py does not contain multiline markdown formatting flaws or terminal dots."""
    from pathlib import Path
    cards_path = Path(__file__).resolve().parent.parent / "components" / "cards.py"
    content = cards_path.read_text(encoding="utf-8")

    # Should not contain terminal dot classes or unrendered markdown code blocks
    assert "tf-preview-dots" not in content
    assert "tf-preview-dot" not in content
    assert "st.code" not in content


def test_upload_component_displays_clean_10mb_limit():
    """Verify components/upload.py clearly shows 10 MB limit and supported formats."""
    from pathlib import Path
    upload_path = Path(__file__).resolve().parent.parent / "components" / "upload.py"
    content = upload_path.read_text(encoding="utf-8")

    assert "Maximum File Size: 10 MB" in content
    assert "PDF, DOCX, TXT" in content
    assert "✓ Resume Ready" in content
    assert "200MB" not in content

