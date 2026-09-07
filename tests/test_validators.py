"""Tests for input validation utilities."""

import pytest
from utils.validators import (
    validate_resume_file, 
    validate_job_description, 
    validate_batch_resumes,
    ValidationResult
)


class MockUploadFile:
    def __init__(self, name: str, size_bytes: int = 1024):
        self.name = name
        self.size = size_bytes
        self._bytes = b"x" * size_bytes

    def getvalue(self) -> bytes:
        return self._bytes


def test_validate_resume_none():
    result = validate_resume_file(None)
    assert not result.is_valid
    assert "upload your resume" in result.message.lower()


def test_validate_resume_unsupported_extension():
    f = MockUploadFile("candidate_photo.png")
    result = validate_resume_file(f)
    assert not result.is_valid
    assert "unsupported" in result.message.lower()


def test_validate_resume_valid_pdf():
    f = MockUploadFile("candidate_resume.pdf")
    result = validate_resume_file(f)
    assert result.is_valid


def test_validate_resume_valid_docx():
    f = MockUploadFile("candidate_resume.docx")
    result = validate_resume_file(f)
    assert result.is_valid


def test_validate_resume_oversized():
    f = MockUploadFile("heavy_file.pdf", size_bytes=15 * 1024 * 1024)
    result = validate_resume_file(f)
    assert not result.is_valid
    assert "exceeds" in result.message.lower()


def test_validate_jd_paste_empty():
    result = validate_job_description("paste", jd_text="")
    assert not result.is_valid
    assert "cannot be empty" in result.message.lower()


def test_validate_jd_paste_too_short():
    result = validate_job_description("paste", jd_text="Need python dev")
    assert not result.is_valid
    assert "too short" in result.message.lower()


def test_validate_jd_paste_valid():
    valid_text = "We are seeking a senior full stack engineer with 4 years of Python and React experience."
    result = validate_job_description("paste", jd_text=valid_text)
    assert result.is_valid


def test_validate_jd_upload_valid():
    f = MockUploadFile("job_spec.txt")
    result = validate_job_description("upload", jd_file=f)
    assert result.is_valid


def test_validate_batch_resumes_empty():
    result = validate_batch_resumes([])
    assert not result.is_valid


def test_validate_batch_resumes_valid():
    files = [
        MockUploadFile("cand_01.pdf"),
        MockUploadFile("cand_02.docx")
    ]
    result = validate_batch_resumes(files)
    assert result.is_valid
    assert "2 candidate resumes" in result.message
