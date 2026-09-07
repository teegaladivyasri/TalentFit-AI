"""Unit tests for ResumeMatcher and explainable scoring."""

import pytest
from services.matcher import ResumeMatcher
from services.scorer import ScorerService
from services.skill_extractor import SkillExtractor
from services.text_preprocessor import TextPreprocessor


@pytest.fixture
def matcher():
    return ResumeMatcher()


@pytest.fixture
def preprocessor():
    return TextPreprocessor()


@pytest.fixture
def extractor():
    return SkillExtractor()


# ---------------------------------------------------------------------------
# 1. Canonical Skill Matching & Overlap
# ---------------------------------------------------------------------------

def test_basic_skill_matching(matcher):
    resume_skills = ["Python", "React", "PostgreSQL", "Docker"]
    jd_skills = ["Python", "React", "AWS"]

    result = matcher.match(resume_skills=resume_skills, jd_skills=jd_skills)
    
    matched_names = [s["skill"] for s in result["matched_skills"]]
    missing_names = [s["skill"] for s in result["missing_skills"]]
    extra_names = [s["skill"] for s in result["extra_skills"]]

    assert "Python" in matched_names
    assert "React" in matched_names
    assert "AWS" in missing_names
    assert "PostgreSQL" in extra_names
    assert "Docker" in extra_names


def test_alias_normalization(matcher, extractor, preprocessor):
    resume_text = "Proficient in python3, postgres, and react.js."
    jd_text = "Requirements: Python, PostgreSQL, and React."

    r_proc = preprocessor.preprocess(resume_text, doc_type="resume")
    j_proc = preprocessor.preprocess(jd_text, doc_type="jd")

    r_skills = extractor.extract(resume_text, sections=r_proc["sections"], document_type="resume")
    j_skills = extractor.extract(jd_text, sections=j_proc["sections"], document_type="jd")

    result = matcher.match(resume_skills=r_skills, jd_skills=j_skills)

    matched_names = [s["skill"] for s in result["matched_skills"]]
    assert "Python" in matched_names
    assert "PostgreSQL" in matched_names
    assert "React" in matched_names
    assert len(result["missing_skills"]) == 0


# ---------------------------------------------------------------------------
# 2. Required vs Preferred Weighting & Numerical Exactness
# ---------------------------------------------------------------------------

def test_required_vs_preferred_weighting(matcher):
    """
    JD:
      Required (1.0 each): Python, FastAPI, PostgreSQL
      Preferred (0.5 each): Docker
      Total JD Weight: 1.0 + 1.0 + 1.0 + 0.5 = 3.5
    Resume:
      Matched: Python (1.0), FastAPI (1.0), Docker (0.5) = 2.5
    Expected Skill Match Score = (2.5 / 3.5) * 100 = 71.42857...
    """
    jd_structured = {
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "details": {
            "Python": {
                "canonical_name": "Python",
                "category": "Programming Languages",
                "occurrences": 2,
                "sections": ["requirements"],
                "evidence": [{"snippet": "Must have strong Python skills", "section": "requirements"}]
            },
            "FastAPI": {
                "canonical_name": "FastAPI",
                "category": "Frameworks",
                "occurrences": 1,
                "sections": ["requirements"],
                "evidence": [{"snippet": "Required FastAPI microservice experience", "section": "requirements"}]
            },
            "PostgreSQL": {
                "canonical_name": "PostgreSQL",
                "category": "Databases",
                "occurrences": 1,
                "sections": ["requirements"],
                "evidence": [{"snippet": "Minimum 2 years PostgreSQL", "section": "requirements"}]
            },
            "Docker": {
                "canonical_name": "Docker",
                "category": "DevOps",
                "occurrences": 1,
                "sections": ["preferred_qualifications"],
                "evidence": [{"snippet": "Docker containerization is a nice to have bonus", "section": "preferred_qualifications"}]
            }
        }
    }

    resume_structured = {
        "skills": ["Python", "FastAPI", "Docker", "Kubernetes"],
        "details": {
            "Python": {"canonical_name": "Python", "category": "Programming Languages", "occurrences": 3, "sections": ["experience"], "evidence": []},
            "FastAPI": {"canonical_name": "FastAPI", "category": "Frameworks", "occurrences": 1, "sections": ["experience"], "evidence": []},
            "Docker": {"canonical_name": "Docker", "category": "DevOps", "occurrences": 2, "sections": ["experience"], "evidence": []},
            "Kubernetes": {"canonical_name": "Kubernetes", "category": "DevOps", "occurrences": 1, "sections": ["experience"], "evidence": []}
        }
    }

    result = matcher.match(resume_skills=resume_structured, jd_skills=jd_structured)

    # 1. Skill Match Score check
    assert result["skill_match_score"] == pytest.approx(71.43, abs=0.01)

    # 2. Required Skills Coverage check: 2 matched out of 3 required (Python, FastAPI matched; PostgreSQL missing)
    # 2 / 3 * 100 = 66.666...
    assert result["required_skill_coverage"] == pytest.approx(66.67, abs=0.01)

    # 3. Verify missing skills
    missing_skills = [s["skill"] for s in result["missing_skills"]]
    assert missing_skills == ["PostgreSQL"]
    assert result["missing_skills"][0]["is_required"] is True

    # 4. Verify extra skills (Kubernetes)
    extra_skills = [s["skill"] for s in result["extra_skills"]]
    assert extra_skills == ["Kubernetes"]


# ---------------------------------------------------------------------------
# 3. TF-IDF Cosine Text Similarity
# ---------------------------------------------------------------------------

def test_tfidf_identical_texts(matcher):
    text = "Senior Software Engineer with extensive Python, Django, PostgreSQL, and AWS experience."
    score = matcher.compute_text_similarity(text, text)
    assert score == pytest.approx(100.0, abs=0.01)


def test_tfidf_overlapping_texts(matcher):
    resume = "Senior Software Engineer experienced with Python, React, PostgreSQL, microservices, and Docker."
    jd = "Looking for a Senior Software Engineer with strong Python, React, Docker, and Kubernetes knowledge."
    score = matcher.compute_text_similarity(resume, jd)
    assert 40.0 <= score <= 90.0


def test_tfidf_completely_unrelated_texts(matcher):
    text_a = "Veterinarian specialized in feline surgery and animal healthcare."
    text_b = "Senior quantitative trading developer with C++ low latency order routing."
    score = matcher.compute_text_similarity(text_a, text_b)
    assert score == pytest.approx(0.0, abs=5.0)


def test_tfidf_empty_and_whitespace_texts(matcher):
    assert matcher.compute_text_similarity("", "Python developer") == 0.0
    assert matcher.compute_text_similarity("Python developer", "") == 0.0
    assert matcher.compute_text_similarity("   ", "   \n\t") == 0.0
    assert matcher.compute_text_similarity(None, "Python") == 0.0


# ---------------------------------------------------------------------------
# 4. Explainable 70/30 Composite Scoring Model
# ---------------------------------------------------------------------------

def test_scorer_composite_formula():
    scorer = ScorerService(skill_weight=0.70, content_weight=0.30)
    
    # Example: Skill Match = 71.43, Content Similarity = 94.12
    # 0.70 * 71.43 + 0.30 * 94.12 = 50.001 + 28.236 = 78.237 -> 78
    rounded, raw, breakdown = scorer.calculate_composite_score(
        skill_match_score=71.43,
        content_similarity_score=94.12
    )
    
    assert rounded == 78
    assert raw == pytest.approx(78.24, abs=0.01)
    assert breakdown["skill_match"]["weight"] == 0.70
    assert breakdown["content_similarity"]["weight"] == 0.30
    assert breakdown["skill_match"]["contribution"] == pytest.approx(50.00, abs=0.01)
    assert breakdown["content_similarity"]["contribution"] == pytest.approx(28.24, abs=0.01)


def test_full_match_scoring_breakdown(matcher):
    resume_skills = ["Python", "FastAPI"]
    jd_skills = ["Python", "FastAPI"]
    resume_text = "Experienced Python FastAPI engineer building backend web services."
    jd_text = "Looking for a Python FastAPI engineer to build backend web services."

    result = matcher.match(
        resume_skills=resume_skills,
        jd_skills=jd_skills,
        resume_text=resume_text,
        jd_text=jd_text
    )

    assert result["skill_match_score"] == 100.0
    assert result["required_skill_coverage"] == 100.0
    assert result["content_similarity_score"] >= 50.0
    assert "score_breakdown" in result
    assert "metadata" in result
    assert result["overall_score"] >= 80


# ---------------------------------------------------------------------------
# 5. Determinism & Idempotence
# ---------------------------------------------------------------------------

def test_matching_determinism(matcher):
    resume_skills = ["Python", "React", "PostgreSQL", "Docker"]
    jd_skills = ["Python", "React", "AWS", "Kubernetes"]
    resume_text = "Senior Python engineer with React and PostgreSQL experience."
    jd_text = "Full Stack role requiring Python, React, AWS, and Kubernetes."

    run1 = matcher.match(resume_skills, jd_skills, resume_text, jd_text)
    run2 = matcher.match(resume_skills, jd_skills, resume_text, jd_text)

    assert run1["overall_score"] == run2["overall_score"]
    assert run1["skill_match_score"] == run2["skill_match_score"]
    assert run1["content_similarity_score"] == run2["content_similarity_score"]
    assert run1["required_skill_coverage"] == run2["required_skill_coverage"]
    assert run1["matched_skills"] == run2["matched_skills"]
    assert run1["missing_skills"] == run2["missing_skills"]
    assert run1["extra_skills"] == run2["extra_skills"]


# ---------------------------------------------------------------------------
# 6. Batch Candidate Ranking & Deterministic Tie-Breaking
# ---------------------------------------------------------------------------

def test_batch_ranking_and_tie_breaking(matcher):
    jd_text = "Senior Python Engineer with PostgreSQL and Docker experience."
    jd_skills = ["Python", "PostgreSQL", "Docker"]

    candidates = [
        {"id": "cand-01", "name": "Charlie", "skills": ["Python", "PostgreSQL"], "text": "Python and PostgreSQL engineer."},
        {"id": "cand-02", "name": "Alice", "skills": ["Python", "PostgreSQL", "Docker"], "text": "Senior Python Engineer with PostgreSQL and Docker."},
        {"id": "cand-03", "name": "Bob", "skills": ["Python", "PostgreSQL"], "text": "Python and PostgreSQL engineer."},
        {"id": "cand-04", "name": "David", "skills": ["Java"], "text": "Java backend developer."},
    ]

    screened = []
    for c in candidates:
        match_res = matcher.match(
            resume_skills=c["skills"],
            jd_skills=jd_skills,
            resume_text=c["text"],
            jd_text=jd_text
        )
        screened.append({
            "id": c["id"],
            "name": c["name"],
            "overall_match": match_res["overall_score"],
            "match_result": match_res
        })

    # Sort deterministically: highest score first, then name alphabetically, then id
    screened.sort(key=lambda x: (-x["overall_match"], x["name"].lower(), x["id"]))

    ranked_names = [c["name"] for c in screened]
    
    # Alice has 100% skill match (highest)
    assert ranked_names[0] == "Alice"
    # Bob and Charlie have identical scores, Bob comes before Charlie alphabetically
    assert ranked_names[1] == "Bob"
    assert ranked_names[2] == "Charlie"
    # David has lowest score
    assert ranked_names[3] == "David"


# ---------------------------------------------------------------------------
# 7. Edge Cases & Malformed Inputs
# ---------------------------------------------------------------------------

def test_extra_skills_do_not_inflate_denominator(matcher):
    """Ensure extra skills in resume do NOT reduce or inflate the JD requirement denominator."""
    jd_skills = ["Python", "React"] # 2 required skills
    # Resume 1 has exactly 2 skills (both matched) -> 100%
    res1 = matcher.match(resume_skills=["Python", "React"], jd_skills=jd_skills)
    # Resume 2 has 2 matched skills + 10 extra skills -> still 100%
    res2 = matcher.match(
        resume_skills=["Python", "React", "Docker", "Kubernetes", "AWS", "GCP", "Redis", "C++", "Java", "Go", "Rust", "GraphQL"], 
        jd_skills=jd_skills
    )
    assert res1["skill_match_score"] == 100.0
    assert res2["skill_match_score"] == 100.0
    assert len(res2["extra_skills"]) == 10


def test_scorer_clamping_and_bounds():
    scorer = ScorerService()
    # Test values above 100 and below 0
    rounded, raw, breakdown = scorer.calculate_composite_score(150.0, -20.0)
    assert rounded == 70 # 0.70 * 100 + 0.30 * 0 = 70
    assert raw == 70.0


def test_matcher_backward_compatible_methods(matcher):
    # compute_skill_overlap
    matched, missing, score = matcher.compute_skill_overlap(["Python", "React"], ["Python", "Docker"])
    assert "Python" in matched
    assert "Docker" in missing
    assert score == 50.0

    # calculate_match
    legacy_res = matcher.calculate_match(
        resume_text="Python and React engineer",
        jd_text="Python and Docker engineer",
        resume_skills=["Python", "React"],
        jd_skills=["Python", "Docker"]
    )
    assert "overall_score" in legacy_res
    assert "matched_skills" in legacy_res
    assert "missing_skills" in legacy_res
    assert "extra_skills" in legacy_res


def test_edge_cases_none_and_empty(matcher):
    # None inputs
    res_none = matcher.match(resume_skills=None, jd_skills=None, resume_text=None, jd_text=None)
    assert res_none["overall_score"] == 0
    assert res_none["skill_match_score"] == 0.0
    assert res_none["content_similarity_score"] == 0.0
    assert res_none["matched_skills"] == []

    # Empty dictionaries
    res_empty_dict = matcher.match(resume_skills={}, jd_skills={}, resume_text="", jd_text="")
    assert res_empty_dict["overall_score"] == 0
    assert res_empty_dict["skill_match_score"] == 0.0

    # JD with 0 skills but resume has skills
    res_jd_empty = matcher.match(resume_skills=["Python", "React"], jd_skills=[], resume_text="Python React", jd_text="General role")
    assert res_jd_empty["matched_skills"] == []
    assert len(res_jd_empty["extra_skills"]) == 2

    # Resume with 0 skills but JD has skills
    res_resume_empty = matcher.match(resume_skills=[], jd_skills=["Python", "SQL"], resume_text="", jd_text="Python SQL")
    assert res_resume_empty["skill_match_score"] == 0.0
    assert len(res_resume_empty["missing_skills"]) == 2
