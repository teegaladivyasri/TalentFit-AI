"""Skill Extractor Service.

Extracts technical and professional skills from resume and Job Description text
using a structured multi-category taxonomy with alias normalization, false-positive protection,
section attribution, and evidence snippet capturing.
"""

import re
import json
from pathlib import Path
from typing import List, Set, Dict, Any, Optional, Tuple, Union


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TAXONOMY_PATH = PROJECT_ROOT / "data" / "skills" / "skills_taxonomy.json"
DEFAULT_FALLBACK_PATH = PROJECT_ROOT / "data" / "skills" / "sample_skills.json"


class SkillExtractor:
    """Production Skill Extraction Engine powered by structured JSON taxonomy."""

    def __init__(self, taxonomy_path: Optional[Union[str, Path]] = None):
        self.taxonomy_path = Path(taxonomy_path) if taxonomy_path else DEFAULT_TAXONOMY_PATH
        self.categories: List[str] = []
        self.skills_db: List[Dict[str, Any]] = []
        self._compiled_patterns: List[Dict[str, Any]] = []
        self._load_taxonomy()

    def _load_taxonomy(self) -> None:
        """Load taxonomy from JSON and build boundary-safe regex patterns."""
        path = self.taxonomy_path
        if not path.exists():
            # Try resolving relative to project root
            relative_candidate = PROJECT_ROOT / path
            if relative_candidate.exists():
                path = relative_candidate
            elif DEFAULT_FALLBACK_PATH.exists():
                path = DEFAULT_FALLBACK_PATH

        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                if "skills" in data:
                    self.categories = data.get("categories", [])
                    self.skills_db = data.get("skills", [])
                else:
                    # Handle flat category -> list format in sample_skills.json
                    self.categories = list(data.keys())
                    self.skills_db = []
                    for cat, skill_names in data.items():
                        for s_name in skill_names:
                            self.skills_db.append({
                                "canonical_name": s_name,
                                "category": cat,
                                "aliases": [s_name.lower()],
                                "priority": "core"
                            })
            except Exception:
                self.categories = []
                self.skills_db = []

        self._build_match_patterns()

    def _build_match_patterns(self) -> None:
        """Compile regex patterns with boundary protection, sorted by phrase length."""
        patterns = []
        
        # Sort skills so more specific multi-word phrases match before shorter sub-phrases
        # e.g., 'React Native' before 'React', 'AWS S3' before 'AWS'
        for entry in self.skills_db:
            canonical = entry["canonical_name"]
            category = entry.get("category", "General")
            aliases = entry.get("aliases", [])
            case_sensitive = entry.get("case_sensitive", False)
            priority = entry.get("priority", "core")
            
            # Combine canonical and aliases
            all_terms = list(set([canonical] + aliases))
            # Sort terms longest first
            all_terms.sort(key=len, reverse=True)
            
            for term in all_terms:
                pattern = self._create_term_regex(term, case_sensitive=case_sensitive)
                if pattern:
                    patterns.append({
                        "canonical_name": canonical,
                        "category": category,
                        "term": term,
                        "term_len": len(term),
                        "pattern": pattern,
                        "case_sensitive": case_sensitive,
                        "priority": priority,
                        "is_canonical": (term.lower() == canonical.lower())
                    })

        # Sort patterns by term length descending
        patterns.sort(key=lambda x: x["term_len"], reverse=True)
        self._compiled_patterns = patterns

    @staticmethod
    def _create_term_regex(term: str, case_sensitive: bool = False) -> Optional[re.Pattern]:
        """Generate precise boundary-aware regex preventing substring false positives."""
        term_clean = term.strip()
        if not term_clean:
            return None

        flags = 0 if case_sensitive else re.IGNORECASE
        
        # 1. Single letter terms (e.g. 'C', 'R')
        if len(term_clean) == 1:
            # Must be standalone letter bounded by non-word/non-symbol or start/end
            return re.compile(rf'(?<![A-Za-z0-9_#+.-])\b{re.escape(term_clean)}\b(?![#+.-])', flags)
            
        # 2. C++
        if term_clean.lower() in ["c++", "cpp", "cplusplus"]:
            return re.compile(r'(?<![A-Za-z0-9_])(?:c\+\+|cpp|cplusplus)(?![A-Za-z0-9_+#])', re.IGNORECASE)
            
        # 3. C#
        if term_clean.lower() in ["c#", "csharp", "c sharp"]:
            return re.compile(r'(?<![A-Za-z0-9_])(?:c\#|csharp|c\s+sharp)(?![A-Za-z0-9_+#])', re.IGNORECASE)
            
        # 4. .NET / ASP.NET
        if term_clean.lower() in [".net", "dotnet", ".net core"]:
            return re.compile(r'(?<![A-Za-z0-9_])(?:\.net\b|dotnet\b|\.net\s+core\b)', re.IGNORECASE)
            
        # 5. React (ensure we don't accidentally swallow React Native if checked)
        if term_clean.lower() in ["react", "react.js", "reactjs", "react js"]:
            return re.compile(r'(?<![A-Za-z0-9_])\b(?:react\.js|reactjs|react\s+js|react)\b(?!\s*native)', re.IGNORECASE)
            
        # 6. React Native
        if term_clean.lower() in ["react native", "react-native"]:
            return re.compile(r'(?<![A-Za-z0-9_])\b(?:react[\s\-]native)\b', re.IGNORECASE)

        # 7. Java (ensure Java does NOT match JavaScript)
        if term_clean.lower() == "java":
            return re.compile(r'(?<![A-Za-z0-9_])\bjava\b(?!\s*script)', re.IGNORECASE)

        # 8. Go / Golang
        if term_clean.lower() in ["go", "golang", "go language"]:
            if term_clean == "Go" and case_sensitive:
                return re.compile(r'(?<![A-Za-z0-9_])\b(?:Go|golang|go\s+language)\b')
            return re.compile(r'(?<![A-Za-z0-9_])\b(?:golang|go\s+language|go\s+lang)\b', re.IGNORECASE)

        # 9. CI/CD
        if term_clean.lower() in ["ci/cd", "ci cd", "cicd"]:
            return re.compile(r'(?<![A-Za-z0-9_])(?:ci\/cd|ci\s+cd|cicd)(?![A-Za-z0-9_])', re.IGNORECASE)

        # 10. General multi-word or punctuated terms (e.g. Node.js, scikit-learn, REST API)
        escaped = re.escape(term_clean)
        escaped = escaped.replace(r"\ ", r"\s+")
        escaped = escaped.replace(r"\-", r"[\s\-]")
        
        return re.compile(rf'(?<![A-Za-z0-9_]){escaped}(?![A-Za-z0-9_])', flags)

    def extract(
        self, 
        text: Optional[str] = None, 
        sections: Optional[Dict[str, str]] = None, 
        document_type: str = "general"
    ) -> Dict[str, Any]:
        """Extract structured, evidence-based, deduplicated skills from document text and sections.
        
        Args:
            text: Full plaintext of the document.
            sections: Optional dictionary of segmented sections (from TextPreprocessor).
            document_type: 'resume', 'jd', or 'general'.
            
        Returns:
            Structured extraction dictionary with canonical skills, categories, and evidence.
        """
        has_text = bool(text and text.strip())
        has_sections = bool(sections and isinstance(sections, dict) and any(v.strip() for v in sections.values()))

        if not has_text and not has_sections:
            return {
                "skills": [],
                "categories": {},
                "details": {},
                "total_occurrences": 0,
                "unique_skills_count": 0
            }

        # Detailed tracking dictionary: canonical_name -> details dict
        detected_details: Dict[str, Dict[str, Any]] = {}

        # Prepare section blocks to scan
        scan_blocks: List[Tuple[str, str]] = []
        if has_sections and sections is not None:
            for sec_name, sec_text in sections.items():
                if sec_text and sec_text.strip():
                    scan_blocks.append((sec_name, sec_text))
        else:
            scan_blocks.append(("content", text or ""))

        # Scan each section block
        for sec_name, block_text in scan_blocks:
            lines = block_text.split("\n")
            
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue

                matched_in_line: Set[str] = set()
                
                for p_info in self._compiled_patterns:
                    canonical = p_info["canonical_name"]
                    pattern = p_info["pattern"]
                    category = p_info["category"]
                    priority = p_info["priority"]
                    
                    matches = list(pattern.finditer(line_str))
                    if matches:
                        matched_in_line.add(canonical)
                        
                        if canonical not in detected_details:
                            detected_details[canonical] = {
                                "canonical_name": canonical,
                                "category": category,
                                "occurrences": 0,
                                "matched_terms": [],
                                "sections": [],
                                "evidence": [],
                                "match_type": "exact" if p_info["is_canonical"] else "alias",
                                "priority": priority
                            }
                            
                        detail = detected_details[canonical]
                        
                        for m in matches:
                            matched_text = m.group(0)
                            detail["occurrences"] += 1
                            if matched_text not in detail["matched_terms"]:
                                detail["matched_terms"].append(matched_text)
                                
                            if sec_name not in detail["sections"]:
                                detail["sections"].append(sec_name)
                                
                            # Keep up to 3 evidence snippets per skill
                            if len(detail["evidence"]) < 3:
                                snippet = line_str if len(line_str) <= 120 else line_str[:117] + "..."
                                detail["evidence"].append({
                                    "section": sec_name,
                                    "matched_term": matched_text,
                                    "snippet": snippet
                                })

        # Compile final structured output
        unique_skills = sorted(list(detected_details.keys()))
        categories_map: Dict[str, List[str]] = {}
        total_occurrences = 0

        for skill_name in unique_skills:
            info = detected_details[skill_name]
            cat = info["category"]
            if cat not in categories_map:
                categories_map[cat] = []
            categories_map[cat].append(skill_name)
            total_occurrences += info["occurrences"]

        return {
            "skills": unique_skills,
            "categories": categories_map,
            "details": detected_details,
            "total_occurrences": total_occurrences,
            "unique_skills_count": len(unique_skills)
        }

    def extract_skills(
        self, 
        text: Optional[str] = None, 
        sections: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """Convenience method returning sorted list of canonical skill names (backward-compatible)."""
        res = self.extract(text, sections=sections)
        return res.get("skills", [])

    def categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Group a list of canonical skill names into taxonomy categories."""
        res: Dict[str, List[str]] = {}
        skill_to_cat = {s["canonical_name"]: s.get("category", "General") for s in self.skills_db}
        
        for s in skills:
            cat = skill_to_cat.get(s, "Technical Skills")
            if cat not in res:
                res[cat] = []
            res[cat].append(s)
            
        return res
