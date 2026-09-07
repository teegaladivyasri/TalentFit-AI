"""Tests for session state management and constants."""

import pytest
from utils.constants import Routes, RecruiterMode, ThemeMode, CandidateStatus
from utils.session_state import DEFAULT_STATE


def test_constants_routes():
    assert Routes.HOME == "home"
    assert Routes.JOB_SEEKER == "job_seeker"
    assert Routes.RECRUITER == "recruiter"
    assert Routes.CANDIDATE_DETAILS == "candidate_details"
    assert Routes.CANDIDATE_COMPARISON == "candidate_comparison"


def test_default_state_keys():
    assert "current_page" in DEFAULT_STATE
    assert "theme" in DEFAULT_STATE
    assert "js_jd_mode" in DEFAULT_STATE
    assert "rec_screening_mode" in DEFAULT_STATE
    assert DEFAULT_STATE["theme"] == ThemeMode.LIGHT
