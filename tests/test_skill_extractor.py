"""Comprehensive unit tests for the SkillExtractor service."""

import pytest
from services.skill_extractor import SkillExtractor


@pytest.fixture
def extractor():
    return SkillExtractor()


# ---------------------------------------------------------------------------
# 1. Basic Skill Extraction
# ---------------------------------------------------------------------------

def test_extract_basic_skills(extractor):
    text = "Experienced software engineer proficient in Python, Java, React, SQL, and AWS."
    skills = extractor.extract_skills(text)
    
    assert "Python" in skills
    assert "Java" in skills
    assert "React" in skills
    assert "SQL" in skills
    assert "AWS" in skills


# ---------------------------------------------------------------------------
# 2. Technical Punctuation and Symbols
# ---------------------------------------------------------------------------

def test_extract_technical_punctuation_skills(extractor):
    text = "Developed microservices with C++, C#, .NET, Node.js, and automated deployment via CI/CD and scikit-learn."
    skills = extractor.extract_skills(text)
    
    assert "C++" in skills
    assert "C#" in skills
    assert ".NET" in skills
    assert "Node.js" in skills
    assert "CI/CD" in skills
    assert "scikit-learn" in skills


# ---------------------------------------------------------------------------
# 3. Alias Normalization to Canonical Names
# ---------------------------------------------------------------------------

def test_extract_alias_normalization(extractor):
    text = "Built web apps using python3, reactjs, nodejs, postgres database, and deployed on gcp with golang backend."
    skills = extractor.extract_skills(text)
    
    assert "Python" in skills
    assert "React" in skills
    assert "Node.js" in skills
    assert "PostgreSQL" in skills
    assert "Google Cloud Platform" in skills
    assert "Go" in skills


# ---------------------------------------------------------------------------
# 4. Strict False-Positive Protection
# ---------------------------------------------------------------------------

def test_false_positive_prevention_c_language(extractor):
    # 'C' should NOT match inside 'developer', 'communication', or 'practices'
    text = "Senior software developer with excellent communication skills and agile practices."
    skills = extractor.extract_skills(text)
    assert "C" not in skills


def test_false_positive_prevention_go_language(extractor):
    # 'Go' should NOT match inside 'Google' or 'good'
    text = "Worked at Google Mountain View building good systems with Python."
    skills = extractor.extract_skills(text)
    assert "Go" not in skills
    assert "Python" in skills


def test_false_positive_prevention_java_vs_javascript(extractor):
    # 'JavaScript' must NOT falsely trigger 'Java'
    text = "Frontend specialist skilled in JavaScript, TypeScript, and HTML/CSS."
    skills = extractor.extract_skills(text)
    assert "JavaScript" in skills
    assert "TypeScript" in skills
    assert "Java" not in skills


def test_false_positive_prevention_react_vs_react_native(extractor):
    # 'React Native' must be recognized as React Native
    text = "Mobile app developer with 3 years of React Native and Swift experience."
    skills = extractor.extract_skills(text)
    assert "React Native" in skills
    assert "Swift" in skills


# ---------------------------------------------------------------------------
# 5. Deduplication and Occurrence Tracking
# ---------------------------------------------------------------------------

def test_skill_deduplication_and_counts(extractor):
    text = """
    Python Developer
    - Programmed Python microservices.
    - Used python3 for data analytics.
    - Mentored team in Python 3 best practices.
    """
    res = extractor.extract(text)
    
    # Must only have 1 canonical 'Python'
    assert "Python" in res["skills"]
    assert res["skills"].count("Python") == 1
    
    # Must track total occurrences across aliases
    py_detail = res["details"]["Python"]
    assert py_detail["canonical_name"] == "Python"
    assert py_detail["occurrences"] >= 3
    assert len(py_detail["evidence"]) >= 1


# ---------------------------------------------------------------------------
# 6. Section-Aware Extraction and Evidence
# ---------------------------------------------------------------------------

def test_section_aware_evidence_tracking(extractor):
    sections = {
        "summary": "5+ years in Python and Docker on AWS.",
        "skills": "Technical Skills: FastAPI, PostgreSQL, Git",
        "experience": "Senior Engineer at Acme:\n- Architected REST APIs with Python and Docker."
    }
    
    res = extractor.extract(text="", sections=sections)
    
    assert "Python" in res["skills"]
    assert "Docker" in res["skills"]
    assert "FastAPI" in res["skills"]
    assert "PostgreSQL" in res["skills"]
    
    py_detail = res["details"]["Python"]
    assert "summary" in py_detail["sections"]
    assert "experience" in py_detail["sections"]
    assert len(py_detail["evidence"]) >= 2
    
    # Check evidence structure
    ev0 = py_detail["evidence"][0]
    assert "section" in ev0
    assert "matched_term" in ev0
    assert "snippet" in ev0


# ---------------------------------------------------------------------------
# 7. Categories Organization
# ---------------------------------------------------------------------------

def test_categories_organization(extractor):
    text = "Proficient in Python, React, PostgreSQL, Docker, and AWS."
    res = extractor.extract(text)
    
    cats = res["categories"]
    assert "Programming Languages" in cats and "Python" in cats["Programming Languages"]
    assert "Web / Frontend" in cats and "React" in cats["Web / Frontend"]
    assert "Databases" in cats and "PostgreSQL" in cats["Databases"]
    assert "DevOps & Infrastructure" in cats and "Docker" in cats["DevOps & Infrastructure"]
    assert "Cloud Platforms & Services" in cats and "AWS" in cats["Cloud Platforms & Services"]


# ---------------------------------------------------------------------------
# 8. Empty and None Inputs
# ---------------------------------------------------------------------------

def test_empty_and_none_input(extractor):
    assert extractor.extract("")["skills"] == []
    assert extractor.extract(None)["skills"] == []
    assert extractor.extract_skills("") == []
    assert extractor.extract_skills(None) == []


# ---------------------------------------------------------------------------
# 9. Determinism
# ---------------------------------------------------------------------------

def test_extraction_determinism(extractor):
    text = "Full Stack Engineer: Python, FastAPI, React, TypeScript, Docker, Kubernetes, PostgreSQL."
    res1 = extractor.extract(text)
    res2 = extractor.extract(text)
    
    assert res1 == res2
    assert res1["skills"] == res2["skills"]
