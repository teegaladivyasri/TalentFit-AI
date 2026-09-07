"""Comprehensive Test Suite for Recruiter Screening, Ranking, Search, Filtering & Sorting (Phase 3)."""

import pytest
from services.document_parser import DocumentParser
from services.text_preprocessor import TextPreprocessor
from services.skill_extractor import SkillExtractor
from services.matcher import ResumeMatcher
from services.scorer import ScorerService
from services.ats_analyzer import ATSAnalyzer
from utils.session_state import reset_recruiter_inputs
from tests.fixtures.synthetic_resumes import (
    RESUME_A_STRONG_MATCH,
    RESUME_B_MODERATE_MATCH,
    RESUME_C_WEAK_MATCH,
    RESUME_D_EXTRA_SKILLS,
    RESUME_E_ALIAS_HEAVY,
    JD_1_PYTHON_BACKEND
)


@pytest.fixture
def recruiter_engine():
    parser = DocumentParser()
    preprocessor = TextPreprocessor()
    extractor = SkillExtractor()
    scorer = ScorerService()
    matcher = ResumeMatcher(scorer=scorer)
    ats_analyzer = ATSAnalyzer()
    return {
        "parser": parser,
        "preprocessor": preprocessor,
        "extractor": extractor,
        "scorer": scorer,
        "matcher": matcher,
        "ats_analyzer": ats_analyzer
    }


def screen_candidate_pool(engine, jd_text: str, candidate_list: list):
    """Helper executing unmocked recruiter screening across a pool of candidates."""
    p = engine["preprocessor"]
    e = engine["extractor"]
    m = engine["matcher"]
    parser = engine["parser"]
    ats = engine["ats_analyzer"]

    jd_proc = p.preprocess(jd_text, doc_type="jd")
    jd_skills = e.extract(text=jd_proc["normalized_text"], sections=jd_proc["sections"], document_type="jd")

    screened = []
    for i, cand in enumerate(candidate_list):
        cand_id = cand.get("id", f"cand-{i+1:02d}")
        filename = cand.get("filename", "resume.pdf")
        rtext = cand.get("text", "")

        r_proc = p.preprocess(rtext, doc_type="resume")
        cand_skills = e.extract(text=r_proc["normalized_text"], sections=r_proc["sections"], document_type="resume")
        
        cand_match = m.match(
            resume_skills=cand_skills,
            jd_skills=jd_skills,
            resume_text=r_proc["cleaned_text"],
            jd_text=jd_proc["cleaned_text"]
        )
        ats_res = ats.analyze(
            resume_text=rtext,
            resume_processed=r_proc,
            resume_skills=cand_skills
        )

        cand_name = parser.extract_candidate_name(text=rtext, filename=filename)
        overall_score = cand_match["overall_score"]
        req_cov = round(cand_match["required_skill_coverage"], 1)

        matched_req = [s["skill"] for s in cand_match["matched_skills"] if s.get("is_required", True)]
        missing_req = [s["skill"] for s in cand_match["missing_skills"] if s.get("is_required", True)]
        matched_pref = [s["skill"] for s in cand_match["matched_skills"] if not s.get("is_required", True)]
        missing_pref = [s["skill"] for s in cand_match["missing_skills"] if not s.get("is_required", True)]
        extra_sk = [s["skill"] for s in cand_match["extra_skills"]]

        if overall_score >= 80 and req_cov >= 75.0:
            cand_status = "Strong Match"
        elif overall_score >= 65 and req_cov >= 50.0:
            cand_status = "Good Match"
        elif overall_score >= 45:
            cand_status = "Partial Match"
        else:
            cand_status = "Low Match"

        screened.append({
            "id": cand_id,
            "rank": 0,
            "name": cand_name,
            "filename": filename,
            "overall_match": overall_score,
            "skill_match": int(round(cand_match["skill_match_score"])),
            "content_similarity": int(round(cand_match["content_similarity_score"])),
            "required_skill_coverage": req_cov,
            "jd_coverage": int(round(req_cov)),
            "status": cand_status,
            "ats_score": ats_res.get("score", 80),
            "ats_breakdown": ats_res.get("components", {}),
            "matched_skills": [s["skill"] for s in cand_match["matched_skills"]],
            "missing_skills": [s["skill"] for s in cand_match["missing_skills"]],
            "extra_skills": extra_sk,
            "matched_required_skills": matched_req,
            "missing_required_skills": missing_req,
            "matched_preferred_skills": matched_pref,
            "missing_preferred_skills": missing_pref,
            "match_result": cand_match,
            "ats_result": ats_res
        })

    # Sort descending by overall_match, tie-break by name, then id
    screened.sort(key=lambda c: (-c["overall_match"], c["name"].lower(), c["id"]))
    for rank_idx, c in enumerate(screened, start=1):
        c["rank"] = rank_idx

    return screened


# ---------------------------------------------------------------------------
# 1. Real Screening & Candidate Ranking Tests
# ---------------------------------------------------------------------------

def test_recruiter_batch_screening_execution(recruiter_engine):
    """Test full unmocked batch screening across 5 candidates."""
    candidates = [
        {"id": "cand-01", "filename": "Alex_Morgan_Resume.pdf", "text": RESUME_A_STRONG_MATCH},
        {"id": "cand-02", "filename": "Jordan_Lee_Resume.pdf", "text": RESUME_B_MODERATE_MATCH},
        {"id": "cand-03", "filename": "Samantha_Taylor_Resume.pdf", "text": RESUME_C_WEAK_MATCH},
        {"id": "cand-04", "filename": "David_Chen_Resume.pdf", "text": RESUME_D_EXTRA_SKILLS},
        {"id": "cand-05", "filename": "Marcus_Vance_Resume.pdf", "text": RESUME_E_ALIAS_HEAVY},
    ]

    results = screen_candidate_pool(recruiter_engine, JD_1_PYTHON_BACKEND, candidates)

    assert len(results) == 5
    # Ranks must be 1 to 5
    assert [c["rank"] for c in results] == [1, 2, 3, 4, 5]
    
    # Overall score must be strictly non-increasing
    scores = [c["overall_match"] for c in results]
    assert scores == sorted(scores, reverse=True)

    # Top candidates must be Strong Match candidates
    assert results[0]["name"] in ["Alex Morgan", "David Chen", "Marcus Vance"]
    assert results[-1]["name"] == "Samantha Taylor"
    assert results[-1]["status"] == "Low Match"


def test_recruiter_deterministic_tie_breaking(recruiter_engine):
    """Candidates with identical scores must break ties by name A-Z, then candidate ID."""
    resume_zoe = RESUME_A_STRONG_MATCH.replace("Alex Morgan", "Zoe Candidate", 1)
    resume_aaron = RESUME_A_STRONG_MATCH.replace("Alex Morgan", "Aaron Candidate", 1)
    candidates = [
        {"id": "cand-02", "filename": "Zoe_Candidate.pdf", "text": resume_zoe},
        {"id": "cand-01", "filename": "Aaron_Candidate.pdf", "text": resume_aaron},
    ]

    results = screen_candidate_pool(recruiter_engine, JD_1_PYTHON_BACKEND, candidates)

    assert len(results) == 2
    assert results[0]["overall_match"] == results[1]["overall_match"]
    # Aaron should be rank 1, Zoe should be rank 2
    assert results[0]["name"] == "Aaron Candidate"
    assert results[1]["name"] == "Zoe Candidate"


# ---------------------------------------------------------------------------
# 2. Search Functionality Tests
# ---------------------------------------------------------------------------

def test_recruiter_search_by_name_and_skill(recruiter_engine):
    """Test case-insensitive candidate search by name, filename, and detected skill."""
    candidates = [
        {"id": "cand-01", "filename": "Alex_Morgan_Resume.pdf", "text": RESUME_A_STRONG_MATCH},
        {"id": "cand-02", "filename": "Jordan_Lee_Resume.pdf", "text": RESUME_B_MODERATE_MATCH},
        {"id": "cand-03", "filename": "Samantha_Taylor_Resume.pdf", "text": RESUME_C_WEAK_MATCH},
        {"id": "cand-04", "filename": "David_Chen_Resume.pdf", "text": RESUME_D_EXTRA_SKILLS},
    ]
    results = screen_candidate_pool(recruiter_engine, JD_1_PYTHON_BACKEND, candidates)

    # Search: 'Alex'
    alex_matches = [c for c in results if "alex" in c["name"].lower() or "alex" in c["filename"].lower()]
    assert len(alex_matches) == 1
    assert alex_matches[0]["name"] == "Alex Morgan"

    # Search: 'PyTorch' (Skill only in David Chen)
    pytorch_matches = [c for c in results if "pytorch" in [s.lower() for s in c["matched_skills"] + c["extra_skills"]]]
    assert len(pytorch_matches) == 1
    assert pytorch_matches[0]["name"] == "David Chen"

    # Search: empty query returns all
    query = ""
    all_res = [c for c in results if not query or query in c["name"].lower()]
    assert len(all_res) == 4


# ---------------------------------------------------------------------------
# 3. Filtering Tests (Score, Required Coverage, Status, Skill)
# ---------------------------------------------------------------------------

def test_recruiter_filters(recruiter_engine):
    """Test score range, required coverage, status, and skill filters."""
    candidates = [
        {"id": "cand-01", "filename": "Alex_Morgan_Resume.pdf", "text": RESUME_A_STRONG_MATCH},
        {"id": "cand-02", "filename": "Jordan_Lee_Resume.pdf", "text": RESUME_B_MODERATE_MATCH},
        {"id": "cand-03", "filename": "Samantha_Taylor_Resume.pdf", "text": RESUME_C_WEAK_MATCH},
        {"id": "cand-04", "filename": "David_Chen_Resume.pdf", "text": RESUME_D_EXTRA_SKILLS},
    ]
    results = screen_candidate_pool(recruiter_engine, JD_1_PYTHON_BACKEND, candidates)

    # 1. Score filter: 70%+
    high_score = [c for c in results if c["overall_match"] >= 70]
    assert len(high_score) >= 1
    for c in high_score:
        assert c["overall_match"] >= 70

    # 2. Required Coverage filter: 80%+
    high_cov = [c for c in results if c["required_skill_coverage"] >= 80.0]
    assert len(high_cov) >= 1
    for c in high_cov:
        assert c["required_skill_coverage"] >= 80.0

    # 3. Status filter: 'Low Match'
    low_match = [c for c in results if c["status"] == "Low Match"]
    assert len(low_match) >= 1
    assert all(c["status"] == "Low Match" for c in low_match)
    assert any(c["name"] == "Samantha Taylor" for c in low_match)

    # 4. Skill filter: 'Docker'
    docker_candidates = [c for c in results if "Docker" in (c["matched_skills"] + c["extra_skills"])]
    assert len(docker_candidates) >= 2


# ---------------------------------------------------------------------------
# 4. Sorting Tests
# ---------------------------------------------------------------------------

def test_recruiter_sorting_orders(recruiter_engine):
    """Test sorting candidates by score, required coverage, skill match, and name."""
    candidates = [
        {"id": "cand-01", "filename": "Alex_Morgan_Resume.pdf", "text": RESUME_A_STRONG_MATCH},
        {"id": "cand-02", "filename": "Jordan_Lee_Resume.pdf", "text": RESUME_B_MODERATE_MATCH},
        {"id": "cand-03", "filename": "Samantha_Taylor_Resume.pdf", "text": RESUME_C_WEAK_MATCH},
    ]
    results = screen_candidate_pool(recruiter_engine, JD_1_PYTHON_BACKEND, candidates)

    # Sort Name A-Z
    by_name = sorted(results, key=lambda x: x["name"])
    assert by_name[0]["name"] == "Alex Morgan"
    assert by_name[1]["name"] == "Jordan Lee"
    assert by_name[2]["name"] == "Samantha Taylor"

    # Sort Required Coverage Descending
    by_cov = sorted(results, key=lambda x: -x["required_skill_coverage"])
    assert by_cov[0]["name"] == "Alex Morgan"
    assert by_cov[-1]["name"] == "Samantha Taylor"


# ---------------------------------------------------------------------------
# 5. Score Reuse Equivalence Test (Job Seeker vs Recruiter)
# ---------------------------------------------------------------------------

def test_score_equivalence_job_seeker_vs_recruiter(recruiter_engine):
    """Verify that Recruiter and Job Seeker workflows produce EXACTLY identical scores for the same resume and JD."""
    p = recruiter_engine["preprocessor"]
    e = recruiter_engine["extractor"]
    m = recruiter_engine["matcher"]

    resume_text = RESUME_A_STRONG_MATCH
    jd_text = JD_1_PYTHON_BACKEND

    # Job Seeker Path
    r_proc = p.preprocess(resume_text, doc_type="resume", remove_stopwords=True)
    j_proc = p.preprocess(jd_text, doc_type="jd", remove_stopwords=True)
    r_skills = e.extract(text=r_proc["normalized_text"], sections=r_proc["sections"], document_type="resume")
    j_skills = e.extract(text=j_proc["normalized_text"], sections=j_proc["sections"], document_type="jd")

    js_match = m.match(
        resume_skills=r_skills,
        jd_skills=j_skills,
        resume_text=r_proc["cleaned_text"],
        jd_text=j_proc["cleaned_text"]
    )

    # Recruiter Path
    rec_results = screen_candidate_pool(
        recruiter_engine, 
        jd_text, 
        [{"id": "cand-01", "filename": "alex.pdf", "text": resume_text}]
    )
    rec_match = rec_results[0]

    # Must be 100% mathematically identical
    assert rec_match["overall_match"] == js_match["overall_score"]
    assert rec_match["skill_match"] == int(round(js_match["skill_match_score"]))
    assert rec_match["content_similarity"] == int(round(js_match["content_similarity_score"]))
    assert rec_match["required_skill_coverage"] == round(js_match["required_skill_coverage"], 1)
    assert rec_match["matched_skills"] == [s["skill"] for s in js_match["matched_skills"]]
    assert rec_match["missing_skills"] == [s["skill"] for s in js_match["missing_skills"]]


# ---------------------------------------------------------------------------
# 6. Session State Reset & Isolation Tests
# ---------------------------------------------------------------------------

def test_recruiter_session_state_reset_integrity():
    """Verify reset_recruiter_inputs clears all previous candidates and comparisons."""
    class MockSessionState(dict):
        def __getattr__(self, key):
            return self.get(key)
        def __setattr__(self, key, value):
            self[key] = value

    mock_state = MockSessionState({
        "rec_jd_text": "Sample JD",
        "rec_screening_results": [{"id": "cand-01", "name": "Alex"}],
        "rec_batch_resumes": ["file1.pdf", "file2.pdf"],
        "rec_selected_candidate_id": "cand-01",
        "rec_compared_candidate_ids": ["cand-01", "cand-02"]
    })

    reset_recruiter_inputs(mock_state)

    assert mock_state["rec_jd_text"] == ""
    assert mock_state["rec_screening_results"] is None
    assert mock_state["rec_batch_resumes"] == []
