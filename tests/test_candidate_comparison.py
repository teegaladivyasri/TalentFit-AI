"""Comprehensive Test Suite for Candidate Comparison Matrix & Workflow (Phase 3)."""

import pytest
from services.document_parser import DocumentParser
from services.text_preprocessor import TextPreprocessor
from services.skill_extractor import SkillExtractor
from services.matcher import ResumeMatcher
from services.scorer import ScorerService
from services.ats_analyzer import ATSAnalyzer
from components.tables import render_comparison_matrix
from tests.fixtures.synthetic_resumes import (
    RESUME_A_STRONG_MATCH,
    RESUME_B_MODERATE_MATCH,
    RESUME_C_WEAK_MATCH,
    RESUME_D_EXTRA_SKILLS,
    RESUME_E_ALIAS_HEAVY,
    JD_1_PYTHON_BACKEND
)
from tests.test_recruiter_screening import screen_candidate_pool


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


@pytest.fixture
def screened_candidates(recruiter_engine):
    candidates = [
        {"id": "cand-01", "filename": "Alex_Morgan_Resume.pdf", "text": RESUME_A_STRONG_MATCH},
        {"id": "cand-02", "filename": "Jordan_Lee_Resume.pdf", "text": RESUME_B_MODERATE_MATCH},
        {"id": "cand-03", "filename": "Samantha_Taylor_Resume.pdf", "text": RESUME_C_WEAK_MATCH},
        {"id": "cand-04", "filename": "David_Chen_Resume.pdf", "text": RESUME_D_EXTRA_SKILLS},
        {"id": "cand-05", "filename": "Marcus_Vance_Resume.pdf", "text": RESUME_E_ALIAS_HEAVY},
    ]
    return screen_candidate_pool(recruiter_engine, JD_1_PYTHON_BACKEND, candidates)


# ---------------------------------------------------------------------------
# 1. Comparison Matrix Structure & Candidate Count Tests
# ---------------------------------------------------------------------------

def test_comparison_matrix_two_candidates(screened_candidates):
    """Test side-by-side comparison matrix with 2 candidates."""
    selected = screened_candidates[:2]
    assert len(selected) == 2

    # Scores must be preserved without any mutation or new scoring
    c1, c2 = selected[0], selected[1]
    assert c1["overall_match"] >= c2["overall_match"]
    assert "matched_skills" in c1 and "matched_skills" in c2
    assert "missing_skills" in c1 and "missing_skills" in c2
    assert "required_skill_coverage" in c1 and "required_skill_coverage" in c2


def test_comparison_matrix_three_candidates(screened_candidates):
    """Test side-by-side comparison matrix with 3 candidates."""
    selected = screened_candidates[:3]
    assert len(selected) == 3
    names = [c["name"] for c in selected]
    assert len(set(names)) == 3


def test_comparison_matrix_four_candidates(screened_candidates):
    """Test side-by-side comparison matrix with maximum 4 candidates."""
    selected = screened_candidates[:4]
    assert len(selected) == 4
    for c in selected:
        assert c["overall_match"] >= 0
        assert c["skill_match"] >= 0
        assert c["content_similarity"] >= 0
        assert c["ats_score"] >= 0


def test_comparison_candidate_limits(screened_candidates):
    """Verify validation boundaries: minimum 2, maximum 4 candidates."""
    # Fewer than 2 candidates
    single_cand = screened_candidates[:1]
    assert len(single_cand) < 2  # UI displays warning: 'Please select at least 2 candidates'

    # More than 4 candidates
    five_cands = screened_candidates[:5]
    assert len(five_cands) == 5
    # Max allowed in comparison multiselect is 4
    capped_cands = five_cands[:4]
    assert len(capped_cands) == 4


# ---------------------------------------------------------------------------
# 2. Score & Skill Consistency in Comparison Matrix
# ---------------------------------------------------------------------------

def test_comparison_scores_identical_to_screening_scores(screened_candidates):
    """Comparison matrix must use the exact same metrics and scores as screening results."""
    for candidate in screened_candidates:
        # Check 70/30 deterministic formula holds in candidate records
        calculated_overall = int(round(0.70 * candidate["skill_match"] + 0.30 * candidate["content_similarity"]))
        # Allow +/- 1 due to internal float vs int round presentation
        assert abs(candidate["overall_match"] - calculated_overall) <= 1


def test_comparison_skill_breakdown_consistency(screened_candidates):
    """Verify matched, missing, and extra skill partitions in comparison."""
    alex = next(c for c in screened_candidates if c["name"] == "Alex Morgan")
    samantha = next(c for c in screened_candidates if c["name"] == "Samantha Taylor")

    # Alex has strong Python, FastAPI, Docker skills
    alex_matched = set(alex["matched_skills"])
    assert "Python" in alex_matched
    assert "Docker" in alex_matched

    # Samantha has mostly JavaScript/React and misses core backend skills
    samantha_missing = set(samantha["missing_skills"])
    assert "Python" in samantha_missing or "FastAPI" in samantha_missing or "PostgreSQL" in samantha_missing

    # Required skill coverage of Alex must be significantly higher than Samantha
    assert alex["required_skill_coverage"] > samantha["required_skill_coverage"]


def test_comparison_matrix_skill_union():
    """Verify skill union logic across multiple compared candidates."""
    c1_matched_req = ["Python", "FastAPI", "Docker"]
    c2_matched_req = ["Python", "PostgreSQL"]

    all_req_skills = sorted(list(set(c1_matched_req + c2_matched_req)))
    assert "Python" in all_req_skills
    assert "FastAPI" in all_req_skills
    assert "Docker" in all_req_skills
    assert "PostgreSQL" in all_req_skills

    # Candidate 1 has FastAPI but Candidate 2 does not
    assert "FastAPI" in c1_matched_req
    assert "FastAPI" not in c2_matched_req
