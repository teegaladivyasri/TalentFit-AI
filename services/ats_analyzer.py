"""ATS Compatibility Analysis Service.

Evaluates resume parse-readiness, structure, contact visibility, skill placement,
and formatting heuristics using a transparent, explainable 5-component scoring model.
"""

import re
from typing import Dict, List, Any, Optional, Set, Tuple


# Type alias for internal scoring tuples (score: float, status: str, detail: str)
TupleScore = Tuple[float, str, str]

# Regex patterns for contact information detection
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_REGEX = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
URL_REGEX = re.compile(r'(?:https?://|www\.|linkedin\.com/in/|github\.com/)[^\s]+', re.IGNORECASE)


class ATSAnalyzer:
    """Production ATS compatibility analyzer evaluating document parse readiness."""

    def __init__(
        self,
        weight_extractability: float = 0.25,
        weight_structure: float = 0.25,
        weight_contact: float = 0.15,
        weight_visibility: float = 0.20,
        weight_organization: float = 0.15
    ):
        self.weight_extractability = weight_extractability
        self.weight_structure = weight_structure
        self.weight_contact = weight_contact
        self.weight_visibility = weight_visibility
        self.weight_organization = weight_organization

    def evaluate_text_extractability(self, text: Optional[str]) -> TupleScore:
        """Evaluate raw text length, word density, and absence of extraction corruption."""
        if not text or not text.strip():
            return 0.0, "Critical", "No extractable text found in document. Parser could not read content."

        clean = text.strip()
        words = clean.split()
        word_count = len(words)
        char_count = len(clean)

        if word_count < 30:
            return 20.0, "Critical", f"Extracted text is extremely sparse ({word_count} words). Potential scan or empty file."
        elif word_count < 100:
            return 55.0, "Low", f"Resume is unusually short ({word_count} words). ATS parsers may miss critical context."
        elif word_count < 180:
            score = 75.0 + ((word_count - 100) / 80.0) * 15.0
            return round(score, 1), "Good", f"Adequate text length ({word_count} words) with standard character density."
        else:
            return 100.0, "Optimal", f"Strong text extractability ({word_count} words, {char_count} characters)."

    def evaluate_section_structure(self, sections: Optional[Dict[str, str]]) -> TupleScore:
        """Evaluate presence of core standard resume sections."""
        if not sections or not isinstance(sections, dict):
            return 20.0, "Low", "No standard section headers could be recognized."

        detected_sections = set(k.lower() for k, v in sections.items() if v and v.strip())
        
        # Primary standard sections (25 pts each = up to 75 pts)
        primary_score = 0.0
        has_skills = any(s in detected_sections for s in ["skills", "technical_skills", "technologies", "core_competencies"])
        has_exp = any(s in detected_sections for s in ["experience", "work_experience", "professional_experience", "employment_history"])
        has_edu = any(s in detected_sections for s in ["education", "academic_background"])

        if has_skills:
            primary_score += 25.0
        if has_exp:
            primary_score += 25.0
        if has_edu:
            primary_score += 25.0

        # Secondary valuable sections (up to 25 pts)
        secondary_score = 0.0
        has_summary = any(s in detected_sections for s in ["summary", "profile", "objective", "about_me"])
        has_projects = any(s in detected_sections for s in ["projects", "technical_projects"])
        has_certs = any(s in detected_sections for s in ["certifications", "licenses"])

        if has_summary:
            secondary_score += 10.0
        if has_projects:
            secondary_score += 10.0
        if has_certs:
            secondary_score += 5.0

        total_structure = min(100.0, primary_score + secondary_score)

        if total_structure >= 85.0:
            status = "Optimal"
            detail = f"Standard core headers detected ({', '.join(sorted(detected_sections))})."
        elif total_structure >= 60.0:
            status = "Good"
            detail = f"Major sections recognized ({', '.join(sorted(detected_sections))})."
        else:
            status = "Needs Attention"
            detail = "Missing one or more foundational sections (Skills, Experience, or Education)."

        return total_structure, status, detail

    def evaluate_contact_information(self, text: Optional[str]) -> TupleScore:
        """Evaluate presence of primary professional contact indicators."""
        if not text:
            return 0.0, "Missing", "No contact details detected."

        has_email = bool(EMAIL_REGEX.search(text))
        has_phone = bool(PHONE_REGEX.search(text))
        has_links = bool(URL_REGEX.search(text) or "linkedin.com" in text.lower() or "github.com" in text.lower())

        score = 0.0
        found = []
        missing = []

        if has_email:
            score += 40.0
            found.append("Email")
        else:
            missing.append("Email")

        if has_phone:
            score += 35.0
            found.append("Phone")
        else:
            missing.append("Phone")

        if has_links:
            score += 25.0
            found.append("Online Profile/Link")
        else:
            missing.append("LinkedIn/Portfolio")

        if score >= 90.0:
            status = "Optimal"
            detail = f"Full contact information detected: {', '.join(found)}."
        elif score >= 65.0:
            status = "Good"
            detail = f"Key contact details found ({', '.join(found)}). Missing: {', '.join(missing)}."
        else:
            status = "Incomplete"
            detail = f"Essential contact details missing ({', '.join(missing)})."

        return score, status, detail

    def evaluate_skill_visibility(
        self, 
        resume_skills: Optional[Any], 
        sections: Optional[Dict[str, str]]
    ) -> TupleScore:
        """Evaluate whether detected skills appear inside structural sections."""
        if not resume_skills:
            return 15.0, "Low", "No technical skills recognized in document."

        # Extract list of skills and details
        if isinstance(resume_skills, dict):
            skills_list = resume_skills.get("skills", [])
            details = resume_skills.get("details", {})
        elif isinstance(resume_skills, list):
            skills_list = resume_skills
            details = {}
        else:
            skills_list = []
            details = {}

        if not skills_list:
            return 15.0, "Low", "No technical skills recognized in document."

        # Check section appearances
        in_skills_section = 0
        in_exp_section = 0

        for s_name in skills_list:
            d = details.get(s_name, {})
            sec_list = d.get("sections", [])
            if any("skill" in s.lower() for s in sec_list):
                in_skills_section += 1
            if any(s.lower() in ["experience", "projects", "work_experience", "technical_projects"] for s in sec_list):
                in_exp_section += 1

        total_skills = len(skills_list)
        skills_sec_ratio = (in_skills_section / total_skills) if total_skills > 0 else 0
        exp_sec_ratio = (in_exp_section / total_skills) if total_skills > 0 else 0

        # Scoring logic
        score = 20.0
        if total_skills >= 5:
            score += 30.0
        elif total_skills >= 2:
            score += 15.0

        if skills_sec_ratio > 0.3:
            score += 30.0
        if exp_sec_ratio > 0.2:
            score += 20.0

        score = min(100.0, score)

        if score >= 80.0:
            status = "Optimal"
            detail = f"{total_skills} skills verified across both dedicated Skills and Experience sections."
        elif score >= 55.0:
            status = "Good"
            detail = f"{total_skills} skills detected, mostly grouped in standard sections."
        else:
            status = "Needs Improvement"
            detail = "Skills appear scattered without strong section consolidation."

        return score, status, detail

    def evaluate_content_organization(self, text: Optional[str]) -> TupleScore:
        """Evaluate bullet formatting, average line lengths, and clean layout markers."""
        if not text or not text.strip():
            return 0.0, "Critical", "Document has no content to evaluate."

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return 0.0, "Critical", "Document has no content lines."

        long_lines = sum(1 for line in lines if len(line) > 300)
        short_lines = sum(1 for line in lines if len(line) < 120)
        total_lines = len(lines)

        # Check for excessive unformatted line wrapping
        long_line_ratio = long_lines / total_lines if total_lines > 0 else 0
        
        score = 85.0
        if long_line_ratio > 0.3:
            score -= 30.0
        elif long_line_ratio > 0.15:
            score -= 15.0

        if total_lines >= 15:
            score += 15.0

        score = max(0.0, min(100.0, score))

        if score >= 80.0:
            status = "Optimal"
            detail = f"Clean line lengths and standard bullet density across {total_lines} content lines."
        elif score >= 60.0:
            status = "Good"
            detail = "Readable formatting with minor long paragraph blocks."
        else:
            status = "Dense"
            detail = "High concentration of long unbroken paragraphs. Use concise bullet points."

        return score, status, detail

    def analyze(
        self,
        resume_text: Optional[str] = None,
        resume_processed: Optional[Dict[str, Any]] = None,
        resume_skills: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive deterministic ATS parse-readiness analysis.
        
        Args:
            resume_text: Raw or normalized resume text.
            resume_processed: Structured dictionary from TextPreprocessor.
            resume_skills: Extracted skills output from SkillExtractor.
            
        Returns:
            Structured ATS findings dictionary with score, components, and actionable advice.
        """
        # Resolve text and sections
        text = resume_text or (resume_processed.get("original_text") if resume_processed else "")
        sections = resume_processed.get("sections") if resume_processed else None

        # 1. Component calculations
        ext_score, ext_status, ext_detail = self.evaluate_text_extractability(text)
        sec_score, sec_status, sec_detail = self.evaluate_section_structure(sections)
        con_score, con_status, con_detail = self.evaluate_contact_information(text)
        vis_score, vis_status, vis_detail = self.evaluate_skill_visibility(resume_skills, sections)
        org_score, org_status, org_detail = self.evaluate_content_organization(text)

        # 2. Weighted overall ATS score
        raw_score = (
            (ext_score * self.weight_extractability) +
            (sec_score * self.weight_structure) +
            (con_score * self.weight_contact) +
            (vis_score * self.weight_visibility) +
            (org_score * self.weight_organization)
        )
        raw_score = max(0.0, min(100.0, raw_score))
        overall_score = int(round(raw_score))

        # 3. Compile strengths, warnings, and recommendations
        strengths: List[str] = []
        warnings: List[str] = []
        recommendations: List[Dict[str, str]] = []

        # Extractability
        if ext_score >= 80.0:
            strengths.append("High text extractability with clean character encodings.")
        else:
            warnings.append("Low text content density detected.")
            recommendations.append({
                "finding": "Extracted text content is shorter than typical professional resumes.",
                "why_it_matters": "Applicant Tracking Systems need sufficient textual context to parse work history and skills.",
                "action": "Ensure your resume document is saved in a standard single-column text format."
            })

        # Section Structure
        if sec_score >= 80.0:
            strengths.append("Standard core headers recognized: Skills, Experience, and Education.")
        else:
            warnings.append("Missing one or more standard resume section headers.")
            recommendations.append({
                "finding": "One or more core section headers (e.g., Technical Skills, Experience) were not clearly identified.",
                "why_it_matters": "ATS parsers look for standard header names to segment your qualifications correctly.",
                "action": "Use clear, conventional headings like 'Technical Skills', 'Work Experience', and 'Education'."
            })

        # Contact Info
        if con_score >= 80.0:
            strengths.append("Contact information (email, phone, online profile) is well-structured and discoverable.")
        else:
            warnings.append("Incomplete professional contact details detected in body text.")
            recommendations.append({
                "finding": "Direct email address or phone number was not detected in parsed body text.",
                "why_it_matters": "Recruiters and automated sourcing tools need immediate access to contact channels.",
                "action": "Place email and phone number in standard plaintext header, avoiding complex embedded header tables."
            })

        # Skill Visibility
        if vis_score >= 80.0:
            strengths.append("Technical skills appear consolidated in a dedicated skills area and supported by experience.")
        else:
            recommendations.append({
                "finding": "Skills are mentioned intermittently without a distinct Technical Skills section.",
                "why_it_matters": "A dedicated skills block enables ATS scanners to index your core technologies immediately.",
                "action": "Group core competencies under a labeled 'Technical Skills' section near the top of your resume."
            })

        # Organization
        if org_score >= 80.0:
            strengths.append("Consistent line lengths and concise bullet point formatting.")
        else:
            recommendations.append({
                "finding": "Long unbroken text paragraphs detected.",
                "why_it_matters": "Dense paragraphs are harder for both automated parsers and human recruiters to skim quickly.",
                "action": "Break multi-sentence paragraphs into concise 1-2 line action-oriented bullet points."
            })

        # 4. Formatted breakdown for UI components
        breakdown_items = {
            "text_extractability": {
                "score": int(round(ext_score)),
                "status": ext_status,
                "detail": ext_detail
            },
            "section_structure": {
                "score": int(round(sec_score)),
                "status": sec_status,
                "detail": sec_detail
            },
            "contact_information": {
                "score": int(round(con_score)),
                "status": con_status,
                "detail": con_detail
            },
            "skill_visibility": {
                "score": int(round(vis_score)),
                "status": vis_status,
                "detail": vis_detail
            },
            "content_organization": {
                "score": int(round(org_score)),
                "status": org_status,
                "detail": org_detail
            }
        }

        return {
            "score": overall_score,
            "raw_score": round(raw_score, 2),
            "components": {
                "text_extractability": round(ext_score, 1),
                "section_structure": round(sec_score, 1),
                "contact_information": round(con_score, 1),
                "skill_visibility": round(vis_score, 1),
                "content_organization": round(org_score, 1)
            },
            "weights": {
                "text_extractability": self.weight_extractability,
                "section_structure": self.weight_structure,
                "contact_information": self.weight_contact,
                "skill_visibility": self.weight_visibility,
                "content_organization": self.weight_organization
            },
            "breakdown_items": breakdown_items,
            "strengths": strengths,
            "warnings": warnings,
            "recommendations": recommendations,
            "is_disclaimer": "This score represents a project-defined parse-readiness indicator based on document extraction and structure heuristics, not a proprietary ATS company guarantee."
        }
