"""Tests verifying mock data consistency and service interface contracts."""

import pytest
from data.mock_data import (
    get_mock_job_seeker_results, 
    get_mock_recruiter_candidates, 
    get_candidate_by_id
)
from services.document_parser import DocumentParser
from services.text_preprocessor import TextPreprocessor
from services.skill_extractor import SkillExtractor
from services.matcher import ResumeMatcher
from services.scorer import ScorerService
from services.recommender import RecommenderService


def test_mock_job_seeker_data_structure():
    results = get_mock_job_seeker_results("Test_Resume.pdf")
    assert "scores" in results
    assert results["scores"]["overall_match"] > 0
    assert "skills" in results
    assert len(results["skills"]["matched"]) > 0
    assert len(results["skills"]["missing"]) > 0
    assert "ats_breakdown" in results
    assert "skills_to_learn" in results


def test_mock_recruiter_candidates_data():
    candidates = get_mock_recruiter_candidates()
    assert len(candidates) >= 4
    for c in candidates:
        assert "id" in c
        assert "name" in c
        assert "overall_match" in c
        assert "skill_match" in c
        assert "status" in c
        assert "matched_skills" in c
        assert "missing_skills" in c


def test_get_candidate_by_id():
    cand = get_candidate_by_id("cand-01")
    assert cand is not None
    assert cand["name"] == "Alex Morgan"


def test_text_preprocessor():
    tp = TextPreprocessor()
    raw = "Senior Software Engineer at https://example.com/jobs! Email: test@acme.com. Skills: Python & React."
    cleaned = tp.clean_text(raw)
    assert "http" not in cleaned
    assert "test@acme.com" not in cleaned
    tokens = tp.tokenize(raw)
    assert "python" in tokens


def test_skill_extractor_stub():
    se = SkillExtractor()
    sample_text = "Proficient in Python, SQL, Docker, and React."
    detected = se.extract_skills(sample_text)
    assert "Python" in detected
    assert "Docker" in detected


def test_resume_matcher_overlap():
    matcher = ResumeMatcher()
    resume_skills = ["Python", "React", "Git"]
    jd_skills = ["Python", "React", "Docker", "AWS"]
    matched, missing, score = matcher.compute_skill_overlap(resume_skills, jd_skills)
    assert "Python" in matched
    assert "Docker" in missing
    assert score == 50.0


def test_scorer_service():
    scorer = ScorerService()
    overall = scorer.calculate_overall_score(skill_score=90.0, content_similarity=80.0, jd_coverage=70.0)
    assert 75.0 <= overall <= 85.0
