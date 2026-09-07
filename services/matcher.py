"""Resume-Job Description Matching and Explainable Scoring Service.

Compares extracted resume skills and text against job description requirements
producing transparent, deterministic, and explainable compatibility scores.
"""

import re
from typing import Dict, List, Set, Any, Tuple, Optional, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from services.scorer import ScorerService


PREFERRED_KEYWORDS = {"preferred", "nice to have", "nice-to-have", "bonus", "desired", "plus", "optional", "asset"}
REQUIRED_KEYWORDS = {"must have", "must-have", "required", "mandatory", "minimum", "essential", "qualification"}


class ResumeMatcher:
    """Production Matching Engine for Resumes and Job Descriptions."""

    def __init__(
        self, 
        scorer: Optional[ScorerService] = None,
        required_weight: float = 1.0,
        preferred_weight: float = 0.5
    ):
        self.scorer = scorer or ScorerService(skill_weight=0.70, content_weight=0.30)
        self.required_weight = required_weight
        self.preferred_weight = preferred_weight

    @staticmethod
    def _parse_skills_input(
        skills_input: Union[List[str], Dict[str, Any], None]
    ) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
        """Normalize skills input into a canonical names list and a details dictionary."""
        if not skills_input:
            return [], {}

        if isinstance(skills_input, dict):
            # Input is structured SkillExtractor output
            skills_list = skills_input.get("skills", [])
            details_map = skills_input.get("details", {})
            return sorted(list(set(skills_list))), details_map

        if isinstance(skills_input, list):
            # Input is flat list of skill strings
            unique_skills = sorted(list(set(s.strip() for s in skills_input if s and s.strip())))
            details_map = {
                s: {
                    "canonical_name": s,
                    "category": "General",
                    "occurrences": 1,
                    "matched_terms": [s],
                    "sections": [],
                    "evidence": [],
                    "priority": "core"
                }
                for s in unique_skills
            }
            return unique_skills, details_map

        return [], {}

    def _classify_jd_skill(
        self, 
        skill_name: str, 
        skill_detail: Dict[str, Any],
        jd_sections: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str, float]:
        """Classify a JD skill as required (1.0) or preferred (0.5).
        
        Returns:
            Tuple of (is_required: bool, priority_label: str, weight: float)
        """
        sections = skill_detail.get("sections", [])
        evidence = skill_detail.get("evidence", [])
        
        # 1. Check if section is explicitly preferred
        for sec in sections:
            sec_lower = sec.lower()
            if "preferred" in sec_lower or "nice" in sec_lower or "bonus" in sec_lower:
                return False, "preferred", self.preferred_weight

        # 2. Check evidence snippets for keywords
        for ev in evidence:
            snippet = ev.get("snippet", "").lower() if isinstance(ev, dict) else str(ev).lower()
            if any(kw in snippet for kw in PREFERRED_KEYWORDS) and not any(rkw in snippet for rkw in REQUIRED_KEYWORDS):
                return False, "preferred", self.preferred_weight

        # 3. Default fallback: skill is required
        return True, "required", self.required_weight

    def compute_text_similarity(self, resume_text: Optional[str], jd_text: Optional[str]) -> float:
        """Calculate TF-IDF cosine similarity between resume text and JD text.
        
        Returns:
            Similarity score normalized as a percentage (0.0 - 100.0).
        """
        if not resume_text or not jd_text:
            return 0.0

        r_text = resume_text.strip()
        j_text = jd_text.strip()

        if not r_text or not j_text:
            return 0.0

        if r_text == j_text:
            return 100.0

        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                token_pattern=r'(?u)\b[a-zA-Z0-9_\-\.\+\#]{2,}\b'
            )
            tfidf_matrix = vectorizer.fit_transform([r_text, j_text])
            
            # If vocabulary is empty
            if tfidf_matrix.shape[1] == 0:
                return 0.0

            sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            raw_sim = float(sim_matrix[0][0])
            score = max(0.0, min(100.0, raw_sim * 100.0))
            return round(score, 2)
        except Exception:
            return 0.0

    def match(
        self,
        resume_skills: Union[List[str], Dict[str, Any], None],
        jd_skills: Union[List[str], Dict[str, Any], None],
        resume_text: Optional[str] = None,
        jd_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive deterministic matching between Resume and JD.
        
        Args:
            resume_skills: Extracted resume skills (list or structured dict).
            jd_skills: Extracted JD skills (list or structured dict).
            resume_text: Optional full/normalized text of resume.
            jd_text: Optional full/normalized text of JD.
            
        Returns:
            Structured explainable match result dictionary.
        """
        r_skills_list, r_details = self._parse_skills_input(resume_skills)
        j_skills_list, j_details = self._parse_skills_input(jd_skills)

        # Build case-insensitive canonical lookup for resume skills
        r_canonical_map = {s.lower(): s for s in r_skills_list}
        j_canonical_map = {s.lower(): s for s in j_skills_list}

        matched_skills: List[Dict[str, Any]] = []
        missing_skills: List[Dict[str, Any]] = []
        extra_skills: List[Dict[str, Any]] = []

        # 1. Process JD skills (Matched vs. Missing)
        matched_weight = 0.0
        total_jd_weight = 0.0
        
        matched_required_count = 0
        total_required_count = 0

        for j_skill in j_skills_list:
            j_detail = j_details.get(j_skill, {})
            is_req, priority_label, weight = self._classify_jd_skill(j_skill, j_detail)
            
            total_jd_weight += weight
            if is_req:
                total_required_count += 1

            # Check if present in resume (case-insensitive canonical match)
            j_lower = j_skill.lower()
            if j_lower in r_canonical_map:
                # Skill is matched
                matched_weight += weight
                if is_req:
                    matched_required_count += 1

                r_canonical_name = r_canonical_map[j_lower]
                r_detail = r_details.get(r_canonical_name, {})

                matched_skills.append({
                    "skill": j_skill,
                    "category": j_detail.get("category") or r_detail.get("category") or "General",
                    "resume_occurrences": r_detail.get("occurrences", 1),
                    "jd_occurrences": j_detail.get("occurrences", 1),
                    "resume_sections": r_detail.get("sections", []),
                    "jd_sections": j_detail.get("sections", []),
                    "resume_evidence": r_detail.get("evidence", []),
                    "jd_evidence": j_detail.get("evidence", []),
                    "is_required": is_req,
                    "priority": priority_label,
                    "weight": weight
                })
            else:
                # Skill is missing from resume
                missing_skills.append({
                    "skill": j_skill,
                    "category": j_detail.get("category", "General"),
                    "jd_occurrences": j_detail.get("occurrences", 1),
                    "jd_sections": j_detail.get("sections", []),
                    "jd_evidence": j_detail.get("evidence", []),
                    "is_required": is_req,
                    "priority": priority_label,
                    "weight": weight
                })

        # 2. Process Extra Resume Skills (in resume but not in JD)
        for r_skill in r_skills_list:
            if r_skill.lower() not in j_canonical_map:
                r_detail = r_details.get(r_skill, {})
                extra_skills.append({
                    "skill": r_skill,
                    "category": r_detail.get("category", "General"),
                    "resume_occurrences": r_detail.get("occurrences", 1),
                    "resume_sections": r_detail.get("sections", []),
                    "resume_evidence": r_detail.get("evidence", [])
                })

        # 3. Calculate Skill Match Score (0.0 - 100.0)
        if total_jd_weight > 0:
            skill_match_score = round((matched_weight / total_jd_weight) * 100.0, 2)
        else:
            # JD has no skills: if resume has skills return 100.0, if both empty return 0.0
            skill_match_score = 100.0 if r_skills_list else 0.0

        # 4. Calculate Required Skills Coverage (0.0 - 100.0)
        if total_required_count > 0:
            required_skill_coverage = round((matched_required_count / total_required_count) * 100.0, 2)
        else:
            required_skill_coverage = 100.0 if r_skills_list else 0.0

        # 5. Calculate Content Similarity Score
        content_sim_score = self.compute_text_similarity(resume_text, jd_text)

        # 6. Calculate Overall Composite Score using 70/30 formula
        rounded_overall, raw_overall, score_breakdown = self.scorer.calculate_composite_score(
            skill_match_score=skill_match_score,
            content_similarity_score=content_sim_score
        )

        required_skills = [s["skill"] for s in (matched_skills + missing_skills) if s["is_required"]]
        preferred_skills = [s["skill"] for s in (matched_skills + missing_skills) if not s["is_required"]]

        return {
            "overall_score": rounded_overall,
            "raw_overall_score": raw_overall,
            "skill_match_score": skill_match_score,
            "content_similarity_score": content_sim_score,
            "required_skill_coverage": required_skill_coverage,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "extra_skills": extra_skills,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "score_weights": {
                "skill_match": self.scorer.skill_weight,
                "content_similarity": self.scorer.content_weight
            },
            "score_breakdown": score_breakdown,
            "metadata": {
                "resume_skill_count": len(r_skills_list),
                "jd_skill_count": len(j_skills_list),
                "matched_skill_count": len(matched_skills),
                "missing_skill_count": len(missing_skills),
                "extra_skill_count": len(extra_skills),
                "required_skill_count": total_required_count,
                "preferred_skill_count": len(j_skills_list) - total_required_count
            }
        }

    def compute_skill_overlap(
        self, 
        resume_skills: List[str], 
        jd_skills: List[str]
    ) -> Tuple[List[str], List[str], float]:
        """Backward-compatible helper returning (matched, missing, skill_score)."""
        res = self.match(resume_skills=resume_skills, jd_skills=jd_skills)
        matched = [s["skill"] for s in res["matched_skills"]]
        missing = [s["skill"] for s in res["missing_skills"]]
        return (matched, missing, res["skill_match_score"])

    def calculate_match(
        self, 
        resume_text: str, 
        jd_text: str, 
        resume_skills: List[str], 
        jd_skills: List[str]
    ) -> Dict[str, Any]:
        """Backward-compatible helper returning match dictionary."""
        res = self.match(
            resume_skills=resume_skills, 
            jd_skills=jd_skills, 
            resume_text=resume_text, 
            jd_text=jd_text
        )
        return {
            "skill_match_score": res["skill_match_score"],
            "content_similarity": res["content_similarity_score"],
            "overall_score": res["overall_score"],
            "matched_skills": [s["skill"] for s in res["matched_skills"]],
            "missing_skills": [s["skill"] for s in res["missing_skills"]],
            "extra_skills": [s["skill"] for s in res["extra_skills"]]
        }
