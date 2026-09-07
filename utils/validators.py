"""Input validation utilities for file uploads and textual inputs."""

from typing import Tuple, List, Optional
from utils.constants import (
    ALLOWED_RESUME_EXTENSIONS,
    ALLOWED_JD_EXTENSIONS,
    MAX_FILE_SIZE_MB,
)

class ValidationResult:
    def __init__(self, is_valid: bool, message: str = ""):
        self.is_valid = is_valid
        self.message = message

    def __bool__(self) -> bool:
        return self.is_valid


def validate_resume_file(uploaded_file) -> ValidationResult:
    """Validate that an uploaded resume exists, has an allowed extension and is within size limits."""
    if uploaded_file is None:
        return ValidationResult(False, "Please upload your resume to proceed.")
    
    filename = getattr(uploaded_file, "name", "")
    extension = filename.split(".")[-1].lower() if "." in filename else ""
    
    if extension not in ALLOWED_RESUME_EXTENSIONS:
        allowed_str = ", ".join(ext.upper() for ext in ALLOWED_RESUME_EXTENSIONS)
        return ValidationResult(
            False, 
            f"Unsupported resume file format (.{extension}). Please upload a {allowed_str} file."
        )
    
    # Check size if available (in bytes)
    size = getattr(uploaded_file, "size", None)
    if size is not None:
        if size == 0:
            return ValidationResult(
                False,
                "The uploaded resume file is empty (0 bytes). Please upload a valid document."
            )
        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if size > max_bytes:
            return ValidationResult(
                False,
                f"File size ({size / (1024*1024):.1f}MB) exceeds the maximum limit of {MAX_FILE_SIZE_MB}MB."
            )
    
    return ValidationResult(True, "Resume file is valid.")


def validate_job_description(
    jd_mode: str, 
    jd_text: Optional[str] = None, 
    jd_file = None
) -> ValidationResult:
    """Validate that a job description is provided either via upload or text paste."""
    if jd_mode == "paste":
        if not jd_text or not jd_text.strip():
            return ValidationResult(False, "Job description text cannot be empty. Please paste the job details.")
        if len(jd_text.strip()) < 30:
            return ValidationResult(
                False, 
                "Job description appears too short. Please provide at least a few sentences describing the role requirements."
            )
        return ValidationResult(True, "Job description text is valid.")
    
    elif jd_mode == "upload":
        if jd_file is None:
            return ValidationResult(False, "Please upload a Job Description document.")
        
        filename = getattr(jd_file, "name", "")
        extension = filename.split(".")[-1].lower() if "." in filename else ""
        
        if extension not in ALLOWED_JD_EXTENSIONS:
            allowed_str = ", ".join(ext.upper() for ext in ALLOWED_JD_EXTENSIONS)
            return ValidationResult(
                False, 
                f"Unsupported JD file format (.{extension}). Please upload a {allowed_str} file."
            )
        
        size = getattr(jd_file, "size", None)
        if size is not None:
            if size == 0:
                return ValidationResult(
                    False,
                    "The uploaded Job Description file is empty (0 bytes). Please upload a valid document."
                )
            max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
            if size > max_bytes:
                return ValidationResult(
                    False,
                    f"JD file size exceeds the maximum limit of {MAX_FILE_SIZE_MB}MB."
                )
            
        return ValidationResult(True, "Job description file is valid.")

    return ValidationResult(False, "Invalid Job Description input mode selected.")


def validate_batch_resumes(uploaded_files: Optional[List]) -> ValidationResult:
    """Validate a batch of candidate resume uploads."""
    if not uploaded_files or len(uploaded_files) == 0:
        return ValidationResult(False, "Please upload at least one candidate resume for batch screening.")
    
    invalid_files = []
    for f in uploaded_files:
        res = validate_resume_file(f)
        if not res.is_valid:
            invalid_files.append(f"{f.name}: {res.message}")
            
    if invalid_files:
        return ValidationResult(False, "Issues detected: " + "; ".join(invalid_files))
        
    return ValidationResult(True, f"{len(uploaded_files)} candidate resumes successfully verified.")
