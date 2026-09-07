"""Unit tests for RecommendationService and career guidance logic."""

import pytest
from services.recommender import RecommendationService
from services.matcher import ResumeMatcher
from services.ats_analyzer import ATSAnalyzer
from utils.constants import SkillPriority


@pytest.fixture
def recommender():
    return RecommendationService()


@pytest.fixture
def matcher():
    return ResumeMatcher()


@pytest.fixture
def ats_analyzer():
    return ATSAnalyzer()


# ---------------------------------------------------------------------------
# 1. Skill Gap Prioritization
# ---------------------------------------------------------------------------

def test_skill_gap_prioritization_required_vs_preferred(recommender):
    missing_skills = [
        {"skill": "Docker", "category": "DevOps", "is_required": False, "priority": "preferred", "jd_occurrences": 1},
        {"skill": "PostgreSQL", "category": "Databases", "is_required": True, "priority": "required", "jd_occurrences": 3},
        {"skill": "FastAPI", "category": "Backend", "is_required": True, "priority": "required", "jd_occurrences": 1}
    ]

    prioritized = recommender.prioritize_missing_skills(missing_skills)

    # 1. Check priority assignment
    assert prioritized[0]["skill"] == "PostgreSQL"
    assert prioritized[0]["priority"] == SkillPriority.HIGH
    assert prioritized[1]["skill"] == "FastAPI"
    assert prioritized[1]["priority"] == SkillPriority.HIGH
    assert prioritized[2]["skill"] == "Docker"
    assert prioritized[2]["priority"] == SkillPriority.MEDIUM


def test_prioritization_string_list_fallback(recommender):
    missing = ["Python", "Docker"]
    prioritized = recommender.prioritize_missing_skills(missing)
    assert len(prioritized) == 2
    assert prioritized[0]["skill"] == "Docker" or prioritized[0]["skill"] == "Python"
    assert prioritized[0]["priority"] == SkillPriority.HIGH


# ---------------------------------------------------------------------------
# 2. Resume Improvement Suggestions & Evidence Gap Detection
# ---------------------------------------------------------------------------

def test_evidence_gap_detection(recommender):
    """When a skill is in Skills section but missing from Experience section, flag it."""
    match_result = {
        "overall_score": 75,
        "matched_skills": [{"skill": "Python"}, {"skill": "React"}],
        "missing_skills": [{"skill": "PostgreSQL", "is_required": True}],
        "extra_skills": []
    }

    resume_skills = {
        "skills": ["Python", "React"],
        "details": {
            # Python appears in both skills and experience
            "Python": {"sections": ["skills", "experience"]},
            # React appears ONLY in skills
            "React": {"sections": ["skills"]}
        }
    }

    suggestions = recommender.generate_resume_suggestions(
        match_result=match_result,
        resume_skills=resume_skills
    )

    improvements_text = " ".join(suggestions["improvements"])
    assert "React" in improvements_text
    assert "Experience" in improvements_text or "experience" in improvements_text


def test_no_fabrication_of_skills(recommender):
    """Suggestions and roadmaps must ONLY reference skills present in input match result."""
    match_result = {
        "overall_score": 80,
        "matched_skills": [{"skill": "Python"}],
        "missing_skills": [{"skill": "FastAPI", "is_required": True}],
        "extra_skills": []
    }

    guidance = recommender.generate(match_result=match_result)
    
    # Check that unrelated skills (e.g. Kotlin, Rust) do not appear in prioritized gaps
    gap_skills = [g["skill"] for g in guidance["prioritized_skill_gaps"]]
    assert "FastAPI" in gap_skills
    assert "Rust" not in gap_skills
    assert "Kotlin" not in gap_skills


# ---------------------------------------------------------------------------
# 3. Learning Roadmap Generation
# ---------------------------------------------------------------------------

def test_learning_roadmap_curated_focus_areas(recommender):
    prioritized = [
        {"skill": "PostgreSQL", "category": "Databases", "priority": SkillPriority.HIGH, "reason": "Missing DB requirement"},
        {"skill": "Docker", "category": "DevOps & Infrastructure", "priority": SkillPriority.MEDIUM, "reason": "Preferred container tool"}
    ]

    roadmap = recommender.generate_learning_roadmap(prioritized)
    assert len(roadmap) == 2
    
    # PostgreSQL focus areas should come from learning_paths.json
    pg_item = roadmap[0]
    assert pg_item["skill"] == "PostgreSQL"
    assert len(pg_item["recommended_focus"]) >= 3
    assert any("SQL" in f or "indexing" in f.lower() or "schema" in f.lower() for f in pg_item["recommended_focus"])

    # Docker focus areas
    docker_item = roadmap[1]
    assert docker_item["skill"] == "Docker"
    assert len(docker_item["recommended_focus"]) >= 3


# ---------------------------------------------------------------------------
# 4. Guidance Headline & Summary Generation
# ---------------------------------------------------------------------------

def test_guidance_headline_thresholds(recommender):
    summary_high = recommender.generate_guidance_summary(85, 90, [], [])
    assert "Strong alignment" in summary_high["headline"]

    summary_mid = recommender.generate_guidance_summary(68, 75, [], [])
    assert "Moderate alignment" in summary_mid["headline"]

    summary_low = recommender.generate_guidance_summary(45, 60, [], [])
    assert "Several important gaps" in summary_low["headline"]


# ---------------------------------------------------------------------------
# 5. Full Pipeline & Determinism
# ---------------------------------------------------------------------------

def test_full_recommender_pipeline_determinism(recommender):
    match_result = {
        "overall_score": 72,
        "matched_skills": [{"skill": "Python", "category": "Programming Languages"}, {"skill": "React", "category": "Web / Frontend"}],
        "missing_skills": [
            {"skill": "PostgreSQL", "category": "Databases", "is_required": True, "priority": "required", "jd_occurrences": 2},
            {"skill": "AWS", "category": "Cloud Platforms & Services", "is_required": False, "priority": "preferred", "jd_occurrences": 1}
        ],
        "extra_skills": [{"skill": "Git", "category": "Version Control"}]
    }

    run1 = recommender.generate(match_result=match_result)
    run2 = recommender.generate(match_result=match_result)

    assert run1["guidance_summary"] == run2["guidance_summary"]
    assert run1["prioritized_skill_gaps"] == run2["prioritized_skill_gaps"]
    assert run1["resume_improvements"] == run2["resume_improvements"]
    assert run1["learning_roadmap"] == run2["learning_roadmap"]


def test_recommender_empty_inputs(recommender):
    res = recommender.generate(match_result={})
    assert res["guidance_summary"]["gap_count"] == 0
    assert res["prioritized_skill_gaps"] == []
    assert res["learning_roadmap"] == []


# ---------------------------------------------------------------------------
# 6. End-to-End Pipeline Integration Test (Section 21 & 23)
# ---------------------------------------------------------------------------

def test_end_to_end_guidance_pipeline(recommender, matcher, ats_analyzer):
    from services.text_preprocessor import TextPreprocessor
    from services.skill_extractor import SkillExtractor

    preprocessor = TextPreprocessor()
    extractor = SkillExtractor()

    jd_text = """
    Senior Python Backend Developer
    
    REQUIREMENTS:
    - Must have strong Python skills
    - Required FastAPI and PostgreSQL experience
    - REST APIs architecture
    
    PREFERRED QUALIFICATIONS:
    - Docker containerization is a plus
    - AWS cloud familiarity
    - Git version control
    """

    resume_text = """
    Jane Doe
    Email: jane.doe@example.com | Phone: 555-123-4567 | LinkedIn: https://linkedin.com/in/janedoe

    PROFESSIONAL SUMMARY
    Python developer with experience building backend APIs.

    TECHNICAL SKILLS
    Python, FastAPI, Git, Docker, REST API

    WORK EXPERIENCE
    Software Engineer at Tech Solutions (2022 - Present)
    - Built REST APIs using Python and FastAPI.
    - Developed backend services for internal applications.

    TECHNICAL PROJECTS
    E-Commerce Microservices
    - Built a Python API application and managed source code with Git.

    EDUCATION
    B.S. in Computer Science, Tech University
    """

    # 1. Preprocessing
    r_proc = preprocessor.preprocess(resume_text, doc_type="resume")
    j_proc = preprocessor.preprocess(jd_text, doc_type="jd")

    # 2. Skill Extraction
    r_skills = extractor.extract(resume_text, sections=r_proc["sections"], document_type="resume")
    j_skills = extractor.extract(jd_text, sections=j_proc["sections"], document_type="jd")

    # 3. Matching & Scoring
    match_result = matcher.match(
        resume_skills=r_skills,
        jd_skills=j_skills,
        resume_text=resume_text,
        jd_text=jd_text
    )

    # 4. ATS Analysis
    ats_result = ats_analyzer.analyze(
        resume_text=resume_text,
        resume_processed=r_proc,
        resume_skills=r_skills
    )

    # 5. Career Guidance & Roadmap
    guidance = recommender.generate(
        match_result=match_result,
        resume_processed=r_proc,
        resume_skills=r_skills,
        jd_processed=j_proc,
        jd_skills=j_skills,
        ats_result=ats_result
    )

    # Verification:
    # Match: Python, FastAPI, Git, Docker, REST API detected
    matched_names = [s["skill"] for s in match_result["matched_skills"]]
    assert "Python" in matched_names
    assert "FastAPI" in matched_names
    assert "Docker" in matched_names
    assert "Git" in matched_names

    # Missing: PostgreSQL, AWS
    missing_names = [s["skill"] for s in match_result["missing_skills"]]
    assert "PostgreSQL" in missing_names
    assert "AWS" in missing_names

    # Priority check: PostgreSQL is HIGH (required), AWS is MEDIUM (preferred)
    prioritized_gaps = guidance["prioritized_skill_gaps"]
    pg_gap = next(g for g in prioritized_gaps if g["skill"] == "PostgreSQL")
    aws_gap = next(g for g in prioritized_gaps if g["skill"] == "AWS")
    assert pg_gap["priority"] == SkillPriority.HIGH
    assert aws_gap["priority"] == SkillPriority.MEDIUM

    # ATS Score is high (clean structure, email, phone, skills, experience)
    assert ats_result["score"] >= 80

    # Resume improvements mentions PostgreSQL
    improvements_str = " ".join(guidance["resume_improvements"])
    assert "PostgreSQL" in improvements_str

    # Learning roadmap contains PostgreSQL and AWS
    roadmap_skills = [item["skill"] for item in guidance["learning_roadmap"]]
    assert "PostgreSQL" in roadmap_skills
    assert "AWS" in roadmap_skills

