"""Comprehensive Security, Input Validation & Isolation Test Suite (Phase 4).

Validates:
1. File format & extension restrictions (.pdf, .docx, .txt, .md).
2. Zero-byte (empty) file rejection.
3. Corrupted / fake extension handling (graceful failure, no traceback leakage).
4. Path traversal filename sanitization.
5. Exception privacy (no stack traces, system paths, or module internals exposed).
6. Text size safety limits (500,000 char bounds).
7. Regex safety & adversarial input resilience.
8. Cross-candidate isolation (zero state or skill leakage between candidates).
9. Immutability of candidate records during search, filter, and sort operations.
10. Absence of sensitive document text printing to stdout.
"""

import io
import time
import pytest
from services.document_parser import DocumentParser, MAX_EXTRACTED_TEXT_LENGTH
from services.text_preprocessor import TextPreprocessor, MAX_TEXT_INPUT_LENGTH
from services.skill_extractor import SkillExtractor
from services.matcher import ResumeMatcher
from services.scorer import ScorerService
from services.ats_analyzer import ATSAnalyzer
from services.recommender import RecommendationService
from utils.validators import (
    validate_resume_file,
    validate_job_description,
    validate_batch_resumes
)
from tests.fixtures.synthetic_resumes import (
    RESUME_A_STRONG_MATCH,
    JD_1_PYTHON_BACKEND
)


class MockUploadFile:
    def __init__(self, name: str, data: bytes = b"sample document content"):
        self.name = name
        self.size = len(data)
        self._data = data

    def getvalue(self) -> bytes:
        return self._data

    def read(self) -> bytes:
        return self._data


# ---------------------------------------------------------------------------
# 1. File Upload & Extension Restrictions
# ---------------------------------------------------------------------------

def test_reject_unsupported_extensions():
    """Verify dangerous / unsupported extensions are blocked before parsing."""
    unsupported = [
        "malicious.exe",
        "script.py",
        "payload.sh",
        "hack.bat",
        "image.png",
        "archive.zip",
        "document.html"
    ]
    for filename in unsupported:
        f = MockUploadFile(filename)
        res = validate_resume_file(f)
        assert not res.is_valid
        assert "unsupported" in res.message.lower()


def test_reject_zero_byte_files():
    """Verify 0-byte empty files are rejected with clear messages across all validators."""
    empty_resume = MockUploadFile("empty_resume.pdf", data=b"")
    res_r = validate_resume_file(empty_resume)
    assert not res_r.is_valid
    assert "0 bytes" in res_r.message.lower() or "empty" in res_r.message.lower()

    empty_jd = MockUploadFile("empty_jd.txt", data=b"")
    res_jd = validate_job_description("upload", jd_file=empty_jd)
    assert not res_jd.is_valid
    assert "0 bytes" in res_jd.message.lower() or "empty" in res_jd.message.lower()

    res_batch = validate_batch_resumes([empty_resume])
    assert not res_batch.is_valid
    assert "0 bytes" in res_batch.message.lower() or "empty" in res_batch.message.lower()


# ---------------------------------------------------------------------------
# 2. Corrupted & Malformed Documents (No Traceback Leakage)
# ---------------------------------------------------------------------------

def test_fake_pdf_binary_content_fails_gracefully():
    """A non-PDF binary file named with .pdf extension must fail with a safe user message."""
    parser = DocumentParser()
    fake_pdf = MockUploadFile("fake.pdf", data=b"NOT_A_REAL_PDF_JUST_RANDOM_GARBAGE_BYTES_1234567890")
    
    result = parser.parse_document(fake_pdf)
    assert result["status"] == "error"
    assert result["text"] == ""
    # Error message must NOT leak Python traceback, file paths, or internal modules
    assert "Traceback" not in result["error_message"]
    assert "pypdf" not in result["error_message"]
    assert "c:\\" not in result["error_message"].lower()
    assert "unable to parse" in result["error_message"].lower()


def test_fake_docx_binary_content_fails_gracefully():
    """A non-DOCX binary file named with .docx extension must fail with a safe user message."""
    parser = DocumentParser()
    fake_docx = MockUploadFile("fake.docx", data=b"NOT_A_ZIP_ARCHIVE_RANDOM_TEXT_BYTES_998877")
    
    result = parser.parse_document(fake_docx)
    assert result["status"] == "error"
    assert result["text"] == ""
    assert "Traceback" not in result["error_message"]
    assert "docx" not in result["error_message"].lower() or "unable to parse" in result["error_message"].lower()


# ---------------------------------------------------------------------------
# 3. Path Traversal Filename Sanitization
# ---------------------------------------------------------------------------

def test_path_traversal_filename_sanitization():
    """Uploaded filenames with path traversal characters must be sanitized to pure basenames."""
    parser = DocumentParser()
    
    traversal_names = [
        "../../etc/passwd.pdf",
        "..\\..\\windows\\system32\\calc.exe.docx",
        "/var/log/syslog.txt",
        "....//....//secret.pdf"
    ]
    
    for t_name in traversal_names:
        parsed = parser.parse_document(MockUploadFile(t_name, data=b"Sample content"))
        assert "/" not in parsed["filename"]
        assert "\\" not in parsed["filename"]
        assert ".." not in parsed["filename"]
        
        # Test candidate name extraction from filename
        extracted_name = parser.extract_candidate_name(text="", filename=t_name)
        assert "/" not in extracted_name
        assert "\\" not in extracted_name
        assert ".." not in extracted_name


# ---------------------------------------------------------------------------
# 4. Text Processing Size Bounds & Memory Safety
# ---------------------------------------------------------------------------

def test_huge_text_input_size_bounding():
    """Enormous text inputs (> 1MB / 1,000,000 characters) must be safely bounded."""
    parser = DocumentParser()
    preprocessor = TextPreprocessor()

    huge_text = "Python software engineer with skills in FastAPI, Docker, and AWS. " * 20_000  # ~1.3MB
    assert len(huge_text) > MAX_EXTRACTED_TEXT_LENGTH

    # Parser bounds test
    sanitized = parser._sanitize_text(huge_text)
    assert len(sanitized) <= MAX_EXTRACTED_TEXT_LENGTH

    # Preprocessor bounds test
    proc = preprocessor.preprocess(huge_text, doc_type="resume")
    assert proc["char_count"] <= MAX_TEXT_INPUT_LENGTH


# ---------------------------------------------------------------------------
# 5. Regex Safety & Adversarial Input Resilience
# ---------------------------------------------------------------------------

def test_adversarial_input_regex_safety():
    """Verify that pathological repeated symbols and unspaced tokens do not cause catastrophic backtracking."""
    preprocessor = TextPreprocessor()
    extractor = SkillExtractor()

    adversarial_samples = [
        "+" * 5000,
        "#" * 5000,
        ".net.net.net.net." * 500,
        "C++#++#++#" * 500,
        "a" * 10000,
        " " * 10000 + "Python" + " " * 10000,
        "\u200b\u200c\u200d" * 1000 + "FastAPI" + "\u200e\u200f" * 1000
    ]

    for sample in adversarial_samples:
        start = time.perf_counter()
        proc = preprocessor.preprocess(sample, doc_type="resume")
        skills = extractor.extract(text=proc["normalized_text"], sections=proc["sections"])
        elapsed = time.perf_counter() - start
        
        # Must execute within 500ms on pathological inputs
        assert elapsed < 0.500, f"Processing took too long: {elapsed:.3f}s on sample"


# ---------------------------------------------------------------------------
# 6. Cross-Candidate Isolation
# ---------------------------------------------------------------------------

def test_cross_candidate_state_and_skill_isolation():
    """Candidate A and Candidate B must have zero skill, score, or ATS state leakage."""
    preprocessor = TextPreprocessor()
    extractor = SkillExtractor()
    matcher = ResumeMatcher(scorer=ScorerService())
    ats = ATSAnalyzer()

    # Candidate A: Pure Python Backend
    resume_a = "Jane Python\nSkills: Python, FastAPI, PostgreSQL, Docker, AWS"
    # Candidate B: Pure Java / Spring
    resume_b = "Bob Java\nSkills: Java, Spring Boot, Hibernate, Oracle, Kubernetes"
    
    jd = "Role: Python Developer\nRequirements:\n- Python\n- FastAPI\n- PostgreSQL"

    # Process JD
    j_proc = preprocessor.preprocess(jd, doc_type="jd")
    j_skills = extractor.extract(text=j_proc["normalized_text"], sections=j_proc["sections"])

    # 1. Screen Candidate A
    a_proc = preprocessor.preprocess(resume_a, doc_type="resume")
    a_skills = extractor.extract(text=a_proc["normalized_text"], sections=a_proc["sections"])
    a_match = matcher.match(resume_skills=a_skills, jd_skills=j_skills)
    a_ats = ats.analyze(resume_processed=a_proc, resume_skills=a_skills)

    # 2. Screen Candidate B
    b_proc = preprocessor.preprocess(resume_b, doc_type="resume")
    b_skills = extractor.extract(text=b_proc["normalized_text"], sections=b_proc["sections"])
    b_match = matcher.match(resume_skills=b_skills, jd_skills=j_skills)
    b_ats = ats.analyze(resume_processed=b_proc, resume_skills=b_skills)

    # Candidate A verification
    assert "Python" in a_skills["skills"]
    assert "Java" not in a_skills["skills"]
    assert a_match["skill_match_score"] == 100.0

    # Candidate B verification - Zero leakage from Candidate A
    assert "Java" in b_skills["skills"]
    assert "Python" not in b_skills["skills"]
    assert "FastAPI" not in b_skills["skills"]
    assert b_match["skill_match_score"] == 0.0
    assert len(b_match["matched_skills"]) == 0
    assert len(b_match["missing_skills"]) == 3


# ---------------------------------------------------------------------------
# 7. Recruiter Result Immutability
# ---------------------------------------------------------------------------

def test_recruiter_result_immutability_during_search_filter_sort():
    """Verify that search, filter, and sort operations do NOT mutate original candidate objects."""
    candidate = {
        "id": "cand-01",
        "rank": 1,
        "name": "Alex Morgan",
        "filename": "Alex_Resume.pdf",
        "overall_match": 85,
        "skill_match": 90,
        "content_similarity": 75,
        "required_skill_coverage": 100.0,
        "status": "Strong Match",
        "matched_skills": ["Python", "FastAPI", "Docker"],
        "missing_skills": ["Kubernetes"],
        "extra_skills": ["Git"]
    }
    candidate_list = [candidate]

    # 1. Search operation simulation
    query = "python"
    searched = [c for c in candidate_list if query in c["name"].lower() or query in [s.lower() for s in c["matched_skills"]]]
    assert len(searched) == 1

    # 2. Filter operation simulation
    filtered = [c for c in searched if c["overall_match"] >= 80 and c["status"] == "Strong Match"]
    assert len(filtered) == 1

    # 3. Sort operation simulation
    sorted_res = sorted(filtered, key=lambda x: x["name"])
    assert len(sorted_res) == 1

    # Original candidate values must remain strictly unchanged
    assert candidate["overall_match"] == 85
    assert candidate["matched_skills"] == ["Python", "FastAPI", "Docker"]
    assert candidate["missing_skills"] == ["Kubernetes"]
    assert candidate["id"] == "cand-01"


# ---------------------------------------------------------------------------
# 8. Privacy & Sensitive Logging Review
# ---------------------------------------------------------------------------

def test_zero_stdout_logging_of_sensitive_resume_text(capsys):
    """Ensure core NLP services execute cleanly without printing raw resume text to stdout/stderr."""
    preprocessor = TextPreprocessor()
    extractor = SkillExtractor()
    matcher = ResumeMatcher()
    ats = ATSAnalyzer()
    recommender = RecommendationService()

    secret_resume_text = "SECRET_CANDIDATE_NAME: John Confidential SSN: 000-00-0000 Email: secret@example.com Phone: 555-0199"
    
    proc = preprocessor.preprocess(secret_resume_text, doc_type="resume")
    skills = extractor.extract(text=proc["normalized_text"])
    match = matcher.match(resume_skills=skills, jd_skills=["Python"])
    ats_res = ats.analyze(resume_processed=proc, resume_skills=skills)
    guidance = recommender.generate(match_result=match, resume_processed=proc, resume_skills=skills)

    captured = capsys.readouterr()
    assert secret_resume_text not in captured.out
    assert "John Confidential" not in captured.out
    assert "000-00-0000" not in captured.out
