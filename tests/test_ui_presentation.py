"""Unit tests for Phase 5 UI Presentation, Score Colors, Badges, and Theme Systems."""

import pytest
from pathlib import Path
from utils.constants import SkillPriority, CandidateStatus, ThemeMode
from components.score import get_score_color, render_priority_badge, render_status_badge


def test_get_score_color_thresholds():
    """Verify semantic hex color mappings based on score brackets."""
    # Score >= 85 -> Emerald
    assert get_score_color(100.0) == "#10B981"
    assert get_score_color(85.0) == "#10B981"
    assert get_score_color(85) == "#10B981"
    
    # 70 <= Score < 85 -> Primary Blue
    assert get_score_color(84.9) == "#2563EB"
    assert get_score_color(70.0) == "#2563EB"
    
    # 55 <= Score < 70 -> Amber
    assert get_score_color(69.9) == "#F59E0B"
    assert get_score_color(55.0) == "#F59E0B"
    
    # Score < 55 -> Rose
    assert get_score_color(54.9) == "#EF4444"
    assert get_score_color(0.0) == "#EF4444"


def test_render_priority_badge():
    """Verify HTML priority pills for HIGH, MEDIUM, LOW skill gaps."""
    high_badge = render_priority_badge(SkillPriority.HIGH)
    assert "tf-priority-pill" in high_badge
    assert "tf-priority-high" in high_badge
    assert "High Priority" in high_badge
    
    med_badge = render_priority_badge(SkillPriority.MEDIUM)
    assert "tf-priority-medium" in med_badge
    assert "Medium Priority" in med_badge
    
    low_badge = render_priority_badge(SkillPriority.LOW)
    assert "tf-priority-low" in low_badge
    assert "Low Priority" in low_badge
    
    # Case insensitivity
    assert "tf-priority-high" in render_priority_badge("high")
    assert "tf-priority-medium" in render_priority_badge("medium")


def test_render_status_badge():
    """Verify candidate status pills have semantic CSS classes and clean icons."""
    strong_badge = render_status_badge("Strong Match")
    assert "tf-status-pill" in strong_badge
    assert "tf-status-recommended" in strong_badge
    assert "✓" in strong_badge
    
    rec_badge = render_status_badge(CandidateStatus.RECOMMENDED)
    assert "tf-status-recommended" in rec_badge
    
    good_badge = render_status_badge("Good Match")
    assert "tf-status-good" in good_badge
    assert "★" in good_badge
    
    review_badge = render_status_badge(CandidateStatus.REVIEW)
    assert "tf-status-good" in review_badge
    
    partial_badge = render_status_badge("Partial Match")
    assert "tf-status-review" in partial_badge
    assert "⚡" in partial_badge
    
    low_badge = render_status_badge("Low Match")
    assert "tf-status-low" in low_badge
    assert "✕" in low_badge


def test_style_css_exists_and_contains_tokens():
    """Verify style.css contains design system tokens and high-contrast button rules."""
    css_path = Path(__file__).resolve().parent.parent / "assets" / "style.css"
    assert css_path.exists(), "assets/style.css must exist"
    
    content = css_path.read_text(encoding="utf-8")
    
    # Verify core design tokens
    assert "--font-sans" in content
    assert "--space-xs" in content
    assert "--space-2xl" in content
    assert "--radius-sm" in content
    assert "--radius-xl" in content
    assert "--bg-surface" in content
    assert "--border-subtle" in content
    assert "--btn-bg" in content
    assert "--btn-text" in content
    assert "--btn-border" in content
    assert "--tag-matched-bg" in content
    assert "--tag-missing-bg" in content
    
    # Verify high contrast button styling rules
    assert ".stButton > button" in content
    assert '[data-testid="stBaseButton-primary"]' in content
    assert '[data-testid="stBaseButton-secondary"]' in content
    
    # Verify UI card and hero classes
    assert ".tf-hero" in content
    assert ".tf-card" in content
    assert ".tf-metric-tile" in content
    assert ".tf-preview-frame" in content
    assert ".tf-highlights-strip" in content


def test_theme_mode_enum():
    """Verify ThemeMode contains LIGHT and DARK."""
    assert ThemeMode.LIGHT == "light"
    assert ThemeMode.DARK == "dark"
