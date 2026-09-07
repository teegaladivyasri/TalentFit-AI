"""Comprehensive unit tests for the TextPreprocessor NLP service."""

import pytest
from services.text_preprocessor import TextPreprocessor


@pytest.fixture
def preprocessor():
    return TextPreprocessor()


# ---------------------------------------------------------------------------
# 1. Empty and None Input Handling
# ---------------------------------------------------------------------------

def test_preprocess_empty_string(preprocessor):
    result = preprocessor.preprocess("")
    assert result["original_text"] == ""
    assert result["normalized_text"] == ""
    assert result["cleaned_text"] == ""
    assert result["tokens"] == []
    assert result["token_count"] == 0
    assert result["sections"] == {}


def test_preprocess_none_input(preprocessor):
    result = preprocessor.preprocess(None)
    assert result["original_text"] == ""
    assert result["tokens"] == []
    assert result["token_count"] == 0


def test_clean_text_empty_and_none(preprocessor):
    assert preprocessor.clean_text("") == ""
    assert preprocessor.clean_text(None) == ""
    assert preprocessor.tokenize("") == []
    assert preprocessor.tokenize(None) == []


# ---------------------------------------------------------------------------
# 2. Unicode and Whitespace Normalization
# ---------------------------------------------------------------------------

def test_normalize_unicode_quotes_and_dashes(preprocessor):
    text = "“Senior” Full–Stack Engineer ‘with’ em—dash & bullet • point"
    normalized = preprocessor.normalize_unicode(text)
    assert '"Senior"' in normalized
    assert "'with'" in normalized
    assert "-" in normalized
    assert "\n" in normalized  # bullet converts to newline separator


def test_normalize_whitespace_and_null_bytes(preprocessor):
    text = "Line 1\x00\x08 with   spaces\r\n\r\n\r\n\r\nLine 2\t\ttabs."
    cleaned = preprocessor.normalize_whitespace(text)
    assert "\x00" not in cleaned
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned
    assert "Line 1 with spaces\n\nLine 2 tabs." in cleaned


# ---------------------------------------------------------------------------
# 3. Preservation of Technical Terminology and Punctuation
# ---------------------------------------------------------------------------

def test_preserve_cpp_and_csharp(preprocessor):
    text = "Experience with C++, C#, and .NET core frameworks."
    tokens = preprocessor.tokenize(text)
    lower_tokens = [t.lower() for t in tokens]
    assert "c++" in lower_tokens
    assert "c#" in lower_tokens
    assert ".net" in lower_tokens


def test_preserve_dotted_and_hyphenated_tech_terms(preprocessor):
    text = "Full-stack development with Node.js, React.js, Next.js, and scikit-learn."
    tokens = preprocessor.tokenize(text)
    lower_tokens = [t.lower() for t in tokens]
    assert "node.js" in lower_tokens
    assert "react.js" in lower_tokens
    assert "next.js" in lower_tokens
    assert "scikit-learn" in lower_tokens
    assert "full-stack" in lower_tokens


def test_preserve_slash_terms_and_versions(preprocessor):
    text = "Implemented CI/CD pipelines and built APIs using Python/FastAPI and OAuth2.0."
    tokens = preprocessor.tokenize(text)
    lower_tokens = [t.lower() for t in tokens]
    assert "ci/cd" in lower_tokens
    assert "python/fastapi" in lower_tokens
    assert "oauth2.0" in lower_tokens


def test_preserve_plus_quantifiers_and_numbers(preprocessor):
    text = "Looking for 5+ years of experience in Python 3.11 with 99.9% uptime."
    tokens = preprocessor.tokenize(text)
    lower_tokens = [t.lower() for t in tokens]
    assert "5+" in lower_tokens
    assert "python" in lower_tokens
    assert "3.11" in lower_tokens


# ---------------------------------------------------------------------------
# 4. Safe Stopword Removal
# ---------------------------------------------------------------------------

def test_safe_stopwords_preserves_tech_words(preprocessor):
    # 'C', 'R', 'Go', 'AI', 'ML' must NOT be stripped as stopwords
    text = "Building AI and ML models with Go, R, and C in the cloud."
    tokens = preprocessor.tokenize(text)
    filtered = preprocessor.remove_stopwords(tokens)
    lower_filtered = [t.lower() for t in filtered]
    
    # Standard words 'and', 'with', 'in', 'the' should be stripped
    assert "and" not in lower_filtered
    assert "in" not in lower_filtered
    assert "the" not in lower_filtered
    
    # Tech words must be strictly preserved
    assert "ai" in lower_filtered
    assert "ml" in lower_filtered
    assert "go" in lower_filtered
    assert "r" in lower_filtered
    assert "c" in lower_filtered
    assert "models" in lower_filtered
    assert "cloud" in lower_filtered


# ---------------------------------------------------------------------------
# 5. Section Extraction
# ---------------------------------------------------------------------------

def test_extract_resume_sections(preprocessor):
    resume_text = """John Doe
Software Engineer
john@example.com

SUMMARY
Passionate engineer with 4 years building scalable distributed web services.

TECHNICAL SKILLS
Languages: Python, JavaScript, TypeScript, SQL
Tools: Docker, Kubernetes, AWS

PROFESSIONAL EXPERIENCE
Senior Developer at CloudTech (2022 - Present)
- Architected REST APIs with FastAPI.

EDUCATION
B.S. in Computer Science, University of California (2020)

TECHNICAL PROJECTS
Distributed Task Queue: Built Redis-backed worker system.
"""
    sections = preprocessor.extract_sections(resume_text, doc_type="resume")
    
    assert "summary" in sections
    assert "skills" in sections
    assert "experience" in sections
    assert "education" in sections
    assert "projects" in sections
    
    assert "Passionate engineer" in sections["summary"]
    assert "Python, JavaScript" in sections["skills"]
    assert "CloudTech" in sections["experience"]
    assert "University of California" in sections["education"]
    assert "Distributed Task Queue" in sections["projects"]


def test_extract_jd_sections(preprocessor):
    jd_text = """Senior Backend Developer
Location: Remote

ABOUT THE ROLE
We are seeking an experienced engineer to lead our core API platform.

KEY RESPONSIBILITIES
- Design and maintain microservices in Python.
- Collaborate with frontend engineers.

REQUIREMENTS & QUALIFICATIONS
- 3+ years professional software development.
- Strong proficiency with PostgreSQL and Docker.

PREFERRED QUALIFICATIONS
- Experience with Kubernetes and Kafka.

BENEFITS
- Competitive salary and health coverage.
"""
    sections = preprocessor.extract_sections(jd_text, doc_type="jd")
    
    assert "summary" in sections
    assert "responsibilities" in sections
    assert "requirements" in sections
    assert "preferred_qualifications" in sections
    assert "benefits" in sections
    
    assert "microservices in Python" in sections["responsibilities"]
    assert "PostgreSQL and Docker" in sections["requirements"]
    assert "Kubernetes and Kafka" in sections["preferred_qualifications"]


# ---------------------------------------------------------------------------
# 6. High-Level Preprocessing Pipeline & Determinism
# ---------------------------------------------------------------------------

def test_preprocess_structured_output_and_preservation(preprocessor):
    raw_sample = "Senior Developer with Python, C++, and Docker experience."
    res = preprocessor.preprocess(raw_sample, doc_type="resume", remove_stopwords=True)
    
    # Verify original text is preserved untouched
    assert res["original_text"] == raw_sample
    
    # Verify cleaned representation exists
    assert "python" in res["cleaned_text"]
    assert "c++" in res["cleaned_text"]
    
    # Verify tokens and filtered tokens
    assert "python" in [t.lower() for t in res["tokens"]]
    assert "c++" in [t.lower() for t in res["tokens"]]
    assert res["token_count"] > 0
    assert len(res["filtered_tokens"]) > 0
    assert res["char_count"] == len(raw_sample)


def test_preprocess_determinism(preprocessor):
    text = "Continuous integration with CI/CD and Docker on AWS cloud."
    res1 = preprocessor.preprocess(text)
    res2 = preprocessor.preprocess(text)
    
    assert res1 == res2
    assert res1["tokens"] == res2["tokens"]
    assert res1["cleaned_text"] == res2["cleaned_text"]
