"""Application constants, route definitions, and configuration values."""

from typing import Dict, List

# Application metadata
APP_TITLE = "TalentFit AI"
APP_SUBTITLE = "Resume Screening & Career Matching Platform"
APP_TAGLINE = "Turn a Job Description into a Clear Career Action Plan"
APP_VERSION = "1.0.0 (Phase 1)"

# Navigation Routes
class Routes:
    HOME = "home"
    JOB_SEEKER = "job_seeker"
    JOB_SEEKER_RESULTS = "job_seeker_results"
    RECRUITER = "recruiter"
    RECRUITER_SCREENING = "recruiter_screening"
    CANDIDATE_DETAILS = "candidate_details"
    CANDIDATE_COMPARISON = "candidate_comparison"

# Screening Modes
class RecruiterMode:
    SINGLE = "single"
    BATCH = "batch"

# File Upload Configuration
ALLOWED_RESUME_EXTENSIONS = ["pdf", "docx", "txt"]
ALLOWED_JD_EXTENSIONS = ["pdf", "docx", "txt"]
MAX_FILE_SIZE_MB = 10

# Candidate Status Types
class CandidateStatus:
    RECOMMENDED = "Recommended"
    REVIEW = "Review"
    LOW_MATCH = "Low Match"

STATUS_COLORS: Dict[str, str] = {
    CandidateStatus.RECOMMENDED: "#10B981",  # Emerald
    CandidateStatus.REVIEW: "#F59E0B",       # Amber
    CandidateStatus.LOW_MATCH: "#EF4444",    # Rose
}

# Skill Priorities
class SkillPriority:
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

# Theme Keys
class ThemeMode:
    LIGHT = "light"
    DARK = "dark"
