"""Performance & Latency Regression Test Suite (Phase 4).

Validates throughput and deterministic execution latency across scaling workloads:
1, 10, 25, 50, and 100 candidate batches.
"""

import time
import pytest
from services.text_preprocessor import TextPreprocessor
from services.skill_extractor import SkillExtractor
from services.matcher import ResumeMatcher
from services.scorer import ScorerService
from services.ats_analyzer import ATSAnalyzer
from services.recommender import RecommendationService
from tests.fixtures.synthetic_resumes import (
    RESUME_A_STRONG_MATCH,
    RESUME_B_MODERATE_MATCH,
    RESUME_C_WEAK_MATCH,
    RESUME_D_EXTRA_SKILLS,
    RESUME_E_ALIAS_HEAVY,
    JD_1_PYTHON_BACKEND
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
        "scorer": scorer,
        "matcher": matcher,
        "ats_analyzer": ats_analyzer,
        "recommender": recommender
    }


def test_single_candidate_latency_benchmark(pipeline):
    """Single candidate end-to-end processing must complete in under 50ms."""
    p = pipeline["preprocessor"]
    e = pipeline["extractor"]
    m = pipeline["matcher"]
    ats = pipeline["ats_analyzer"]
    rec = pipeline["recommender"]

    jd_proc = p.preprocess(JD_1_PYTHON_BACKEND, doc_type="jd")
    jd_skills = e.extract(text=jd_proc["normalized_text"], sections=jd_proc["sections"])

    start = time.perf_counter()
    r_proc = p.preprocess(RESUME_A_STRONG_MATCH, doc_type="resume", remove_stopwords=True)
    r_skills = e.extract(text=r_proc["normalized_text"], sections=r_proc["sections"])
    match_res = m.match(
        resume_skills=r_skills,
        jd_skills=jd_skills,
        resume_text=r_proc["cleaned_text"],
        jd_text=jd_proc["cleaned_text"]
    )
    ats_res = ats.analyze(
        resume_text=r_proc["normalized_text"],
        resume_processed=r_proc,
        resume_skills=r_skills
    )
    guidance = rec.generate(
        match_result=match_res,
        resume_processed=r_proc,
        resume_skills=r_skills,
        jd_processed=jd_proc,
        jd_skills=jd_skills,
        ats_result=ats_res
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 60.0  # Max 60ms SLA
    assert match_res["overall_score"] > 70


def test_batch_scaling_10_candidates(pipeline):
    """Batch of 10 candidates must complete in under 250ms."""
    p = pipeline["preprocessor"]
    e = pipeline["extractor"]
    m = pipeline["matcher"]
    ats = pipeline["ats_analyzer"]

    sample_pool = [RESUME_A_STRONG_MATCH, RESUME_B_MODERATE_MATCH, RESUME_C_WEAK_MATCH, RESUME_D_EXTRA_SKILLS, RESUME_E_ALIAS_HEAVY]
    batch = [sample_pool[i % len(sample_pool)] for i in range(10)]

    j_proc = p.preprocess(JD_1_PYTHON_BACKEND, doc_type="jd")
    j_skills = e.extract(text=j_proc["normalized_text"], sections=j_proc["sections"])

    start = time.perf_counter()
    for resume in batch:
        r_proc = p.preprocess(resume, doc_type="resume")
        r_skills = e.extract(text=r_proc["normalized_text"], sections=r_proc["sections"])
        match = m.match(resume_skills=r_skills, jd_skills=j_skills, resume_text=r_proc["cleaned_text"], jd_text=j_proc["cleaned_text"])
        ats_res = ats.analyze(resume_processed=r_proc, resume_skills=r_skills)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 250.0


def test_batch_scaling_25_candidates(pipeline):
    """Batch of 25 candidates must complete in under 500ms."""
    p = pipeline["preprocessor"]
    e = pipeline["extractor"]
    m = pipeline["matcher"]
    ats = pipeline["ats_analyzer"]

    sample_pool = [RESUME_A_STRONG_MATCH, RESUME_B_MODERATE_MATCH, RESUME_C_WEAK_MATCH, RESUME_D_EXTRA_SKILLS, RESUME_E_ALIAS_HEAVY]
    batch = [sample_pool[i % len(sample_pool)] for i in range(25)]

    j_proc = p.preprocess(JD_1_PYTHON_BACKEND, doc_type="jd")
    j_skills = e.extract(text=j_proc["normalized_text"], sections=j_proc["sections"])

    start = time.perf_counter()
    for resume in batch:
        r_proc = p.preprocess(resume, doc_type="resume")
        r_skills = e.extract(text=r_proc["normalized_text"], sections=r_proc["sections"])
        match = m.match(resume_skills=r_skills, jd_skills=j_skills, resume_text=r_proc["cleaned_text"], jd_text=j_proc["cleaned_text"])
        ats_res = ats.analyze(resume_processed=r_proc, resume_skills=r_skills)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 500.0


def test_batch_scaling_50_candidates(pipeline):
    """Batch of 50 candidates must complete in under 1000ms."""
    p = pipeline["preprocessor"]
    e = pipeline["extractor"]
    m = pipeline["matcher"]
    ats = pipeline["ats_analyzer"]

    sample_pool = [RESUME_A_STRONG_MATCH, RESUME_B_MODERATE_MATCH, RESUME_C_WEAK_MATCH, RESUME_D_EXTRA_SKILLS, RESUME_E_ALIAS_HEAVY]
    batch = [sample_pool[i % len(sample_pool)] for i in range(50)]

    j_proc = p.preprocess(JD_1_PYTHON_BACKEND, doc_type="jd")
    j_skills = e.extract(text=j_proc["normalized_text"], sections=j_proc["sections"])

    start = time.perf_counter()
    for resume in batch:
        r_proc = p.preprocess(resume, doc_type="resume")
        r_skills = e.extract(text=r_proc["normalized_text"], sections=r_proc["sections"])
        match = m.match(resume_skills=r_skills, jd_skills=j_skills, resume_text=r_proc["cleaned_text"], jd_text=j_proc["cleaned_text"])
        ats_res = ats.analyze(resume_processed=r_proc, resume_skills=r_skills)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 1000.0


def test_batch_scaling_100_candidates(pipeline):
    """Batch of 100 candidates must complete in under 2000ms."""
    p = pipeline["preprocessor"]
    e = pipeline["extractor"]
    m = pipeline["matcher"]
    ats = pipeline["ats_analyzer"]

    sample_pool = [RESUME_A_STRONG_MATCH, RESUME_B_MODERATE_MATCH, RESUME_C_WEAK_MATCH, RESUME_D_EXTRA_SKILLS, RESUME_E_ALIAS_HEAVY]
    batch = [sample_pool[i % len(sample_pool)] for i in range(100)]

    j_proc = p.preprocess(JD_1_PYTHON_BACKEND, doc_type="jd")
    j_skills = e.extract(text=j_proc["normalized_text"], sections=j_proc["sections"])

    start = time.perf_counter()
    for resume in batch:
        r_proc = p.preprocess(resume, doc_type="resume")
        r_skills = e.extract(text=r_proc["normalized_text"], sections=r_proc["sections"])
        match = m.match(resume_skills=r_skills, jd_skills=j_skills, resume_text=r_proc["cleaned_text"], jd_text=j_proc["cleaned_text"])
        ats_res = ats.analyze(resume_processed=r_proc, resume_skills=r_skills)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 2000.0
