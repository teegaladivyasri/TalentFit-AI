"""Unit tests for ATSAnalyzer service."""

import pytest
from services.ats_analyzer import ATSAnalyzer
from services.text_preprocessor import TextPreprocessor
from services.skill_extractor import SkillExtractor


@pytest.fixture
def analyzer():
    return ATSAnalyzer()


@pytest.fixture
def preprocessor():
    return TextPreprocessor()


@pytest.fixture
def extractor():
    return SkillExtractor()


# ---------------------------------------------------------------------------
# 1. Text Extractability
# ---------------------------------------------------------------------------

def test_extractability_optimal_text(analyzer):
    text = "Word " * 200 # 200 words
    score, status, detail = analyzer.evaluate_text_extractability(text)
    assert score == 100.0
    assert status == "Optimal"


def test_extractability_sparse_text(analyzer):
    text = "Short resume text with just a few words."
    score, status, detail = analyzer.evaluate_text_extractability(text)
    assert score <= 30.0
    assert status == "Critical"


def test_extractability_empty_and_none(analyzer):
    score_empty, status_empty, _ = analyzer.evaluate_text_extractability("")
    score_none, status_none, _ = analyzer.evaluate_text_extractability(None)
    assert score_empty == 0.0
    assert score_none == 0.0


# ---------------------------------------------------------------------------
# 2. Section Structure
# ---------------------------------------------------------------------------

def test_section_structure_full_core_sections(analyzer):
    sections = {
        "skills": "Python, React, SQL",
        "experience": "Software Engineer at Acme",
        "education": "BS in Computer Science",
        "summary": "Experienced engineer",
        "projects": "Open source tools"
    }
    score, status, detail = analyzer.evaluate_section_structure(sections)
    assert score >= 90.0
    assert status == "Optimal"


def test_section_structure_missing_core_sections(analyzer):
    # Only summary and projects, missing skills, experience, education
    sections = {
        "summary": "About me",
        "projects": "Project A"
    }
    score, status, detail = analyzer.evaluate_section_structure(sections)
    assert score < 50.0
    assert status == "Needs Attention"


def test_section_structure_empty(analyzer):
    score, status, _ = analyzer.evaluate_section_structure({})
    assert score <= 20.0


# ---------------------------------------------------------------------------
# 3. Contact Information Detection
# ---------------------------------------------------------------------------

def test_contact_information_full(analyzer):
    text = "John Doe\nEmail: john.doe@example.com\nPhone: +1 (555) 123-4567\nLinkedIn: https://linkedin.com/in/johndoe"
    score, status, detail = analyzer.evaluate_contact_information(text)
    assert score == 100.0
    assert status == "Optimal"


def test_contact_information_partial(analyzer):
    # Email only
    text = "Alex Smith\nEmail: alex@example.com\nSummary: Software developer."
    score, status, detail = analyzer.evaluate_contact_information(text)
    assert score == 40.0
    assert "Phone" in detail


def test_contact_information_missing(analyzer):
    text = "Jane Doe\nSummary: Software engineer with experience in web applications."
    score, status, detail = analyzer.evaluate_contact_information(text)
    assert score == 0.0
    assert status == "Incomplete"


# ---------------------------------------------------------------------------
# 4. Skill Visibility
# ---------------------------------------------------------------------------

def test_skill_visibility_in_both_skills_and_exp(analyzer):
    resume_skills = {
        "skills": ["Python", "React", "PostgreSQL", "Docker", "Git"],
        "details": {
            "Python": {"sections": ["skills", "experience"]},
            "React": {"sections": ["skills", "projects"]},
            "PostgreSQL": {"sections": ["skills", "experience"]},
            "Docker": {"sections": ["skills"]},
            "Git": {"sections": ["skills", "experience"]}
        }
    }
    sections = {"skills": "Python, React", "experience": "Used Python and PostgreSQL"}
    score, status, detail = analyzer.evaluate_skill_visibility(resume_skills, sections)
    assert score >= 85.0
    assert status == "Optimal"


def test_skill_visibility_none(analyzer):
    score, status, detail = analyzer.evaluate_skill_visibility(None, {})
    assert score <= 20.0
    assert status == "Low"


# ---------------------------------------------------------------------------
# 5. Full ATS Analysis & Determinism
# ---------------------------------------------------------------------------

def test_full_ats_analysis_calculation(analyzer, preprocessor, extractor):
    resume_text = """
    John Doe
    Email: john@example.com | Phone: 555-987-6543 | LinkedIn: https://linkedin.com/in/johndoe

    SUMMARY
    Senior Software Engineer with 5+ years of full-stack development experience.

    TECHNICAL SKILLS
    Python, FastAPI, React, PostgreSQL, Docker, Git

    WORK EXPERIENCE
    Senior Engineer at Acme Corp (2021 - Present)
    - Developed backend microservices using Python and FastAPI.
    - Designed relational database schemas in PostgreSQL.
    - Containerized application services with Docker for CI/CD workflows.

    EDUCATION
    B.S. in Computer Science, University of Technology (2017 - 2021)

    PROJECTS
    Full Stack E-Commerce Application
    - Built responsive frontend with React and backend API with Python.
    """
    
    proc = preprocessor.preprocess(resume_text, doc_type="resume")
    skills = extractor.extract(resume_text, sections=proc["sections"], document_type="resume")

    result = analyzer.analyze(
        resume_text=resume_text,
        resume_processed=proc,
        resume_skills=skills
    )

    assert result["score"] >= 80
    assert "components" in result
    assert "breakdown_items" in result
    assert len(result["strengths"]) > 0
    assert "text_extractability" in result["components"]
    assert "section_structure" in result["components"]
    assert "contact_information" in result["components"]
    assert "skill_visibility" in result["components"]
    assert "content_organization" in result["components"]


def test_ats_analysis_determinism(analyzer, preprocessor, extractor):
    text = "Alex Smith\nEmail: alex@example.com\n\nSKILLS\nPython, React\n\nEXPERIENCE\nBuilt apps in Python."
    proc = preprocessor.preprocess(text, doc_type="resume")
    skills = extractor.extract(text, sections=proc["sections"], document_type="resume")

    res1 = analyzer.analyze(resume_text=text, resume_processed=proc, resume_skills=skills)
    res2 = analyzer.analyze(resume_text=text, resume_processed=proc, resume_skills=skills)

    assert res1["score"] == res2["score"]
    assert res1["raw_score"] == res2["raw_score"]
    assert res1["components"] == res2["components"]
