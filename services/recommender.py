"""Career Guidance & Recommendation Service.

Generates deterministic skill gap prioritizations, actionable resume improvement suggestions,
and personalized learning roadmaps based on resume-JD matching and ATS analysis results.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from utils.constants import SkillPriority
from services.ats_analyzer import ATSAnalyzer


# Fallback focus areas by category if specific skill is not in knowledge base
CATEGORY_FALLBACK_FOCUS = {
    "Programming Languages": [
        "Core syntax, data structures, and memory/type models",
        "Idiomatic coding patterns and object-oriented / functional paradigms",
        "Unit testing, packaging, and dependency management",
        "Concurrency, asynchronous programming, and standard library tools"
    ],
    "Web / Frontend": [
        "Component architecture, props, and state management",
        "DOM lifecycle, event handling, and reactive rendering",
        "Responsive styling, layout systems, and web accessibility (a11y)",
        "Build optimization, bundling, and client-side testing"
    ],
    "Backend / APIs": [
        "RESTful API design conventions, routing, and HTTP semantics",
        "Data validation, serialization, and ORM / query integration",
        "Authentication, authorization (JWT/OAuth2), and middleware",
        "Error handling, logging, and asynchronous request processing"
    ],
    "Databases": [
        "Relational / Document schema design and normalization",
        "Query construction, complex joins, and aggregation pipelines",
        "Indexing strategies, query execution analysis, and performance tuning",
        "ACID transactions, concurrency control, and migrations"
    ],
    "Cloud Platforms & Services": [
        "Core compute, storage, and managed service architectures",
        "Serverless execution, API gateways, and event-driven patterns",
        "Identity & Access Management (IAM) and network security (VPC)",
        "Monitoring, metrics logging, and cost optimization"
    ],
    "DevOps & Infrastructure": [
        "Containerization best practices and multi-stage builds",
        "Orchestration, pod/service definitions, and cluster deployment",
        "CI/CD pipeline automation and automated test stages",
        "Infrastructure as Code (IaC) and configuration management"
    ],
    "Data / AI / ML": [
        "Data preprocessing, feature engineering, and exploratory analysis",
        "Model training, evaluation metrics, and hyperparameter tuning",
        "Pipeline construction and model serialization",
        "Responsible AI practices, validation splits, and monitoring"
    ],
    "Version Control": [
        "Branching workflows, trunk-based development, and rebase strategies",
        "Merge conflict resolution and history inspection",
        "Pull request reviews and semantic commit conventions",
        "Git hooks and automated CI integration"
    ],
    "Security": [
        "OWASP Top 10 vulnerabilities and mitigation strategies",
        "Encryption at rest and in transit, TLS/SSL configuration",
        "Secure credential storage, secrets rotation, and audit logging",
        "Role-based access control (RBAC) and least privilege principles"
    ],
    "Professional / Engineering Skills": [
        "System architecture decomposition and trade-off analysis",
        "Agile delivery, code review standards, and technical documentation",
        "Scalability, caching tiers, and high-availability design",
        "Root-cause debugging, observability, and performance profiling"
    ]
}


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEARNING_PATHS_PATH = PROJECT_ROOT / "data" / "skills" / "learning_paths.json"


class RecommendationService:
    """Production Recommendation & Guidance Engine for Job Seekers."""

    def __init__(
        self, 
        learning_paths_path: Optional[Union[str, Path]] = None,
        ats_analyzer: Optional[ATSAnalyzer] = None
    ):
        self.learning_paths_path = Path(learning_paths_path) if learning_paths_path else DEFAULT_LEARNING_PATHS_PATH
        self.ats_analyzer = ats_analyzer or ATSAnalyzer()
        self.learning_paths: Dict[str, Any] = {}
        self._load_learning_paths()

    def _load_learning_paths(self) -> None:
        """Load curated skill learning focus areas from JSON."""
        path = self.learning_paths_path
        if not path.exists():
            relative_candidate = PROJECT_ROOT / path
            if relative_candidate.exists():
                path = relative_candidate

        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.learning_paths = json.load(f)
            except Exception:
                self.learning_paths = {}

    def prioritize_missing_skills(
        self, 
        missing_skills: Union[List[str], List[Dict[str, Any]], None]
    ) -> List[Dict[str, Any]]:
        """Prioritize missing JD skills into HIGH, MEDIUM, and LOW tiers.
        
        Rules:
            - HIGH: Required skills explicitly demanded in JD requirements.
            - MEDIUM: Preferred / bonus qualifications.
            - LOW: Optional / peripheral competencies.
            
        Sorting:
            Priority (HIGH -> MEDIUM -> LOW) -> Required before Preferred -> JD occurrences (descending) -> Skill name (A-Z).
        """
        if not missing_skills:
            return []

        prioritized: List[Dict[str, Any]] = []

        for item in missing_skills:
            if isinstance(item, dict):
                skill_name = item.get("skill", "")
                category = item.get("category", "Technical Skills")
                is_req = item.get("is_required", True)
                priority_val = item.get("priority", "required")
                jd_occ = item.get("jd_occurrences", 1)
                jd_evidence = item.get("jd_evidence", [])
            else:
                skill_name = str(item)
                category = "Technical Skills"
                is_req = True
                priority_val = "required"
                jd_occ = 1
                jd_evidence = []

            if not skill_name:
                continue

            # Assign Priority
            if is_req or priority_val == "required" or priority_val == SkillPriority.HIGH:
                assigned_priority = SkillPriority.HIGH
                reason = "Required by target role specifications but not detected in resume."
            elif priority_val == "preferred" or priority_val == SkillPriority.MEDIUM:
                assigned_priority = SkillPriority.MEDIUM
                reason = "Preferred qualification requested by employer that enhances candidate competitiveness."
            else:
                assigned_priority = SkillPriority.LOW
                reason = "Optional competency referenced in job description specifications."

            rec_action = (
                f"If you possess professional experience with {skill_name}, ensure it is clearly listed in your Technical Skills "
                f"and described in your Experience bullets; otherwise prioritize learning it."
            )

            prioritized.append({
                "skill": skill_name,
                "category": category,
                "priority": assigned_priority,
                "is_required": is_req,
                "jd_occurrences": jd_occ,
                "reason": reason,
                "jd_evidence": jd_evidence,
                "recommended_action": rec_action
            })

        # Deterministic sort order
        priority_rank = {SkillPriority.HIGH: 0, SkillPriority.MEDIUM: 1, SkillPriority.LOW: 2}
        prioritized.sort(
            key=lambda x: (
                priority_rank.get(x["priority"], 3),
                0 if x["is_required"] else 1,
                -x["jd_occurrences"],
                x["skill"].lower()
            )
        )

        return prioritized

    def generate_resume_suggestions(
        self,
        match_result: Optional[Dict[str, Any]] = None,
        resume_processed: Optional[Dict[str, Any]] = None,
        resume_skills: Optional[Dict[str, Any]] = None,
        ats_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate actionable, evidence-based strengths and improvement points.
        
        Never tells the candidate to fabricate experience or lie about skills.
        """
        strengths: List[str] = []
        improvements: List[str] = []
        detailed_recs: List[Dict[str, Any]] = []

        m_result = match_result or {}
        matched = m_result.get("matched_skills", [])
        missing = m_result.get("missing_skills", [])
        extra = m_result.get("extra_skills", [])
        score = m_result.get("overall_score", 0)

        # 1. Strengths Generation
        if matched:
            top_matched_names = [s["skill"] if isinstance(s, dict) else str(s) for s in matched[:4]]
            strengths.append(
                f"Verified alignment on key role requirements: {', '.join(top_matched_names)}."
            )

        if extra:
            extra_names = [s["skill"] if isinstance(s, dict) else str(s) for s in extra[:3]]
            strengths.append(
                f"Possesses relevant additional technical competencies ({', '.join(extra_names)}) that add breadth to your profile."
            )

        if ats_result and ats_result.get("strengths"):
            strengths.extend(ats_result["strengths"][:2])

        if not strengths:
            strengths.append("Foundational technical background extracted from submitted documentation.")

        # 2. Improvement: Skill Gaps
        req_missing = [s for s in missing if isinstance(s, dict) and s.get("is_required", True)]
        if req_missing:
            req_names = [s["skill"] for s in req_missing[:3]]
            improvements.append(
                f"Core role requirements ({', '.join(req_names)}) were not detected in your resume. "
                f"If you have experience with these technologies, make them explicit in your Technical Skills section."
            )
            for rm in req_missing[:2]:
                detailed_recs.append({
                    "type": "skill_gap",
                    "category": "Skills",
                    "priority": SkillPriority.HIGH,
                    "title": f"Address Missing Requirement: {rm['skill']}",
                    "description": f"The job description specifies {rm['skill']} as a key qualification.",
                    "reason": "Missing core requirements significantly reduce automated match compatibility.",
                    "action": f"If you have used {rm['skill']}, detail your practical application; otherwise prioritize it in your learning plan.",
                    "source": "job_description"
                })

        # 3. Improvement: Experience Evidence Check
        # Check if skills appear in 'skills' section but lack occurrences in 'experience'/'projects'
        if resume_skills and isinstance(resume_skills, dict):
            r_details = resume_skills.get("details", {})
            evidence_gaps = []
            for s_info in matched:
                s_name = s_info["skill"] if isinstance(s_info, dict) else str(s_info)
                detail = r_details.get(s_name, {})
                sections_present = detail.get("sections", [])
                has_skills_sec = any("skill" in s.lower() for s in sections_present)
                has_exp_sec = any(s.lower() in ["experience", "projects", "work_experience"] for s in sections_present)
                
                if has_skills_sec and not has_exp_sec:
                    evidence_gaps.append(s_name)

            if evidence_gaps:
                top_gap = evidence_gaps[0]
                improvements.append(
                    f"'{top_gap}' is listed in your Skills section, but supporting work experience or project evidence was not detected. "
                    f"Consider adding a concise bullet point describing a practical project where you applied '{top_gap}'."
                )
                detailed_recs.append({
                    "type": "evidence_gap",
                    "category": "Experience Evidence",
                    "priority": SkillPriority.MEDIUM,
                    "title": f"Add Experience Evidence for {top_gap}",
                    "description": f"{top_gap} is listed as a skill, but has no detailed bullet point context.",
                    "reason": "Hiring managers value demonstrated impact over standalone skill lists.",
                    "action": f"Add a concise bullet point showing how you utilized {top_gap} to achieve measurable results.",
                    "source": "resume"
                })

        # 4. Improvement: ATS Heuristics
        if ats_result:
            for rec in ats_result.get("recommendations", [])[:2]:
                improvements.append(f"{rec['finding']} {rec['action']}")
                detailed_recs.append({
                    "type": "ats_heuristic",
                    "category": "Resume Structure",
                    "priority": SkillPriority.MEDIUM,
                    "title": rec["finding"],
                    "description": rec["why_it_matters"],
                    "reason": rec["why_it_matters"],
                    "action": rec["action"],
                    "source": "ats_analysis"
                })

        if not improvements:
            improvements.append(
                "Continue refining bullet points with quantifiable metrics and business impact to maximize recruiter engagement."
            )

        # 5. Structured Section-by-Section Improvements
        section_improvements: Dict[str, List[str]] = {}

        # Technical Skills Section
        if req_missing:
            req_names = [s["skill"] if isinstance(s, dict) else str(s) for s in req_missing[:4]]
            section_improvements["Technical Skills"] = [
                f"If you have hands-on experience with missing JD requirements ({', '.join(req_names)}), ensure they are explicitly listed in your Technical Skills section.",
                "Organize skills clearly into categories (e.g., Languages, Frameworks, Databases, Cloud & Tools) for readability and ATS parsing."
            ]
        elif missing:
            miss_names = [s["skill"] if isinstance(s, dict) else str(s) for s in missing[:3]]
            section_improvements["Technical Skills"] = [
                f"If you possess experience with requested technologies ({', '.join(miss_names)}), explicitly add them to your Technical Skills section.",
                "Ensure your strongest relevant technical proficiencies appear near the top of your resume."
            ]
        else:
            section_improvements["Technical Skills"] = [
                "Your Technical Skills section successfully aligns with all primary technologies detected in the Job Description."
            ]

        # Work Experience Section
        if matched:
            top_m = [s["skill"] if isinstance(s, dict) else str(s) for s in matched[:3]]
            section_improvements["Work Experience"] = [
                f"Mention target role technologies directly in your experience bullet points where used (e.g., instead of 'Developed backend services', write 'Developed RESTful backend services using {top_m[0]} and {top_m[1] if len(top_m) > 1 else 'modern conventions'}').",
                "Quantify achievements wherever possible with metrics, performance gains, or scale numbers."
            ]
        else:
            section_improvements["Work Experience"] = [
                "Rewrite relevant experience bullets to directly demonstrate practical application of role responsibilities.",
                "Highlight quantifiable outcomes and specific technologies utilized in your work history."
            ]

        # Projects Section
        if missing:
            top_miss = [s["skill"] if isinstance(s, dict) else str(s) for s in missing[:2]]
            section_improvements["Projects"] = [
                f"Highlight practical projects that demonstrate hands-on application of target technologies like {', '.join(top_miss)}.",
                "Provide concise summaries of problem statements, architectural approaches, and links to public repositories if available."
            ]
        else:
            section_improvements["Projects"] = [
                "Feature 2–3 key projects that demonstrate mastery of the required architecture, testing standards, and tools."
            ]

        # Professional Summary
        section_improvements["Professional Summary"] = [
            "Align your summary title and opening statement with the target role, highlighting relevant years of experience and core competencies.",
            "Use exact terminology from the Job Description when it accurately reflects your genuine background."
        ]

        return {
            "strengths": strengths,
            "improvements": improvements,
            "section_improvements": section_improvements,
            "detailed_recommendations": detailed_recs
        }

    def generate_learning_roadmap(
        self,
        prioritized_skills: List[Dict[str, Any]],
        max_skills: int = 6
    ) -> List[Dict[str, Any]]:
        """Generate tailored learning focus areas, practical exercises, and project ideas for missing JD skills."""
        if not prioritized_skills:
            return []

        curated_projects = {
            "AWS": "Deploy a containerized FastAPI application using AWS EC2, S3, and configure basic IAM security policies.",
            "Docker": "Write a multi-stage Dockerfile for a backend API and configure multi-container orchestration with Docker Compose.",
            "Kubernetes": "Deploy a scalable microservice on a local Minikube/Kind cluster with Service, Deployment, and ConfigMap manifests.",
            "PostgreSQL": "Design a relational schema with indexing, complex JOIN queries, transactions, and migration scripts.",
            "FastAPI": "Build an asynchronous RESTful API with Pydantic request validation, dependency injection, and automated OpenAPI docs.",
            "React": "Build an interactive dashboard component with state hooks, custom responsive layouts, and REST API integration.",
            "Redis": "Implement caching middleware and session storage for backend API endpoints using Redis key-value structures.",
            "GraphQL": "Build a GraphQL API with typed schemas, queries, mutations, and resolvers connecting to a relational database.",
            "TypeScript": "Convert a JavaScript project to TypeScript with strict type definitions, generics, and interface contracts.",
            "Python": "Build an end-to-end data processing service with clean object-oriented architecture and unit testing."
        }

        roadmap: List[Dict[str, Any]] = []

        for item in prioritized_skills[:max_skills]:
            skill_name = item.get("skill", "")
            category = item.get("category", "General")
            priority = item.get("priority", SkillPriority.HIGH)
            reason = item.get("reason", "Required target competency.")

            # Look up curated focus areas from knowledge base
            curated_entry = self.learning_paths.get(skill_name)
            if curated_entry and "focus_areas" in curated_entry:
                focus_areas = curated_entry["focus_areas"]
            else:
                # Category fallback or generic default
                focus_areas = CATEGORY_FALLBACK_FOCUS.get(
                    category,
                    [
                        f"Core principles and fundamentals of {skill_name}",
                        f"Hands-on implementation and practical project development",
                        f"Integration with modern tech stacks and best practices",
                        f"Testing, optimization, and real-world deployment patterns"
                    ]
                )

            learning_sequence = [
                f"1. Understand core concepts, syntax, and architectural conventions of {skill_name}.",
                f"2. Follow official tutorials to set up a working local development environment.",
                f"3. Build a standalone proof-of-concept module exercising key operations.",
                f"4. Integrate {skill_name} with your existing tech stack or backend data layers.",
                f"5. Add automated unit tests, error handling, and deploy a working demonstration."
            ]

            how_to_practice = f"Follow official documentation and structured tutorials to build a standalone proof-of-concept incorporating {skill_name}."
            practice_project = curated_projects.get(
                skill_name, 
                f"Build a practical mini-project utilizing {skill_name} and integrate it with your existing stack."
            )
            
            search_phrases = [
                f'"{skill_name} official tutorial"',
                f'"{skill_name} beginner guide"',
                f'"{skill_name} hands-on project tutorial"'
            ]

            resource_types = [
                f"Official {skill_name} Documentation & Guides",
                f"freeCodeCamp / Official Developer Portals for {skill_name}",
                f"GitHub Open-Source Examples using {skill_name}"
            ]

            roadmap.append({
                "skill": skill_name,
                "category": category,
                "priority": priority,
                "reason": reason,
                "recommended_focus": focus_areas,
                "what_to_learn": focus_areas,
                "learning_sequence": learning_sequence,
                "how_to_practice": how_to_practice,
                "practice_project": practice_project,
                "search_phrases": search_phrases,
                "resource_types": resource_types,
                "where_to_learn": resource_types
            })

        return roadmap

    def generate_guidance_summary(
        self,
        overall_score: int,
        ats_score: int,
        prioritized_gaps: List[Dict[str, Any]],
        improvements: List[str]
    ) -> Dict[str, Any]:
        """Generate high-level candidate guidance summary and situational headline."""
        if overall_score >= 80:
            headline = "Strong alignment with this role. Focus on addressing the remaining skill gaps and refining resume evidence."
        elif overall_score >= 60:
            headline = "Moderate alignment. Strengthen the missing high-priority skills and improve role-specific experience evidence."
        else:
            headline = "Several important gaps were detected. Focus on developing high-priority core competencies before targeting similar roles."

        top_gaps = [g["skill"] for g in prioritized_gaps[:3]]
        
        return {
            "headline": headline,
            "overall_score": overall_score,
            "ats_score": ats_score,
            "top_gaps": top_gaps,
            "gap_count": len(prioritized_gaps),
            "top_improvements": improvements[:3]
        }

    def generate(
        self,
        match_result: Dict[str, Any],
        resume_processed: Optional[Dict[str, Any]] = None,
        resume_skills: Optional[Dict[str, Any]] = None,
        jd_processed: Optional[Dict[str, Any]] = None,
        jd_skills: Optional[Dict[str, Any]] = None,
        ats_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute full candidate career guidance and recommendation pipeline.
        
        Returns:
            Structured career guidance payload with ATS analysis, prioritized gaps,
            actionable improvements, section improvements, and structured learning roadmap.
        """
        # 1. Ensure ATS analysis exists
        if not ats_result:
            ats_res = self.ats_analyzer.analyze(
                resume_processed=resume_processed,
                resume_skills=resume_skills
            )
        else:
            ats_res = ats_result

        # 2. Prioritize missing skills
        missing_skills_input = match_result.get("missing_skills", [])
        prioritized_gaps = self.prioritize_missing_skills(missing_skills_input)

        # 3. Generate actionable suggestions
        suggestions = self.generate_resume_suggestions(
            match_result=match_result,
            resume_processed=resume_processed,
            resume_skills=resume_skills,
            ats_result=ats_res
        )

        # 4. Generate learning roadmap
        roadmap = self.generate_learning_roadmap(prioritized_gaps)

        # 5. Generate high-level summary
        overall_score = match_result.get("overall_score", 0)
        ats_score = ats_res.get("score", 0)
        guidance_summary = self.generate_guidance_summary(
            overall_score=overall_score,
            ats_score=ats_score,
            prioritized_gaps=prioritized_gaps,
            improvements=suggestions.get("improvements", [])
        )

        return {
            "guidance_summary": guidance_summary,
            "ats_result": ats_res,
            "prioritized_skill_gaps": prioritized_gaps,
            "resume_strengths": suggestions.get("strengths", []),
            "resume_improvements": suggestions.get("improvements", []),
            "section_improvements": suggestions.get("section_improvements", {}),
            "detailed_recommendations": suggestions.get("detailed_recommendations", []),
            "learning_roadmap": roadmap
        }


# Alias for backward compatibility with stub imports
RecommenderService = RecommendationService
