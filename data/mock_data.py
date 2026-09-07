"""Mock data module providing realistic data models for Phase 1 UI scaffolding."""

from typing import Dict, List, Any, Optional
from utils.constants import CandidateStatus, SkillPriority


# Default sample Job Description for testing and prepopulation
SAMPLE_JOB_DESCRIPTION = """Role: Senior Full Stack Engineer (Python & React)
Location: San Francisco, CA (Hybrid) / Remote

About the Role:
We are seeking an experienced Full Stack Engineer to architect and build scalable web applications. You will collaborate with product designers, data engineers, and frontend specialists to deliver high-performance user experiences.

Key Responsibilities:
- Design and develop robust backend microservices and RESTful APIs using Python (FastAPI / Django).
- Build responsive, accessible frontend interfaces with React, TypeScript, and modern state management.
- Manage relational and NoSQL databases including PostgreSQL and Redis for high-throughput data processing.
- Containerize applications using Docker and orchestrate workloads with Kubernetes on AWS cloud infrastructure.
- Implement automated testing, continuous integration, and continuous deployment (CI/CD) pipelines.

Requirements & Qualifications:
- 3+ years of professional software engineering experience in full-stack web development.
- Strong proficiency in Python and modern JavaScript/TypeScript (React).
- Hands-on experience with SQL databases (PostgreSQL) and database schema design.
- Familiarity with containerization (Docker), cloud services (AWS), and CI/CD best practices.
- Excellent communication skills, system architecture thinking, and collaborative team mindset.
"""


def get_mock_job_seeker_results(resume_name: Optional[str] = None) -> Dict[str, Any]:
    """Return mock analysis results for the Job Seeker workflow."""
    return {
        "candidate_name": "Jordan Taylor",
        "resume_filename": resume_name or "Jordan_Taylor_Resume.pdf",
        "target_role": "Senior Full Stack Engineer",
        "target_company": "Acme Tech Inc.",
        "analysis_date": "2026-09-06",
        "scores": {
            "overall_match": 78,
            "skill_match": 85,
            "content_similarity": 72,
            "jd_coverage": 80,
            "ats_score": 82,
        },
        "ats_breakdown": {
            "keyword_coverage": {
                "score": 86,
                "status": "Strong",
                "detail": "86% of primary keywords from the job description are present in standard sections."
            },
            "section_completeness": {
                "score": 90,
                "status": "Optimal",
                "detail": "Standard headers detected: Summary, Technical Skills, Experience, Education, Projects."
            },
            "formatting_readability": {
                "score": 78,
                "status": "Good",
                "detail": "Single-column layout with consistent hierarchy. Ensure font sizes remain between 10-12pt."
            },
            "terminology_relevance": {
                "score": 84,
                "status": "Strong",
                "detail": "High density of industry-standard tech stack and architecture terminology."
            }
        },
        "skills": {
            "matched": [
                "Python", "SQL", "React", "Git", "RESTful APIs", 
                "FastAPI", "PostgreSQL", "Docker", "JavaScript", "TypeScript"
            ],
            "missing": [
                "Kubernetes", "CI/CD", "AWS", "GraphQL", "Redis"
            ]
        },
        "resume_strengths": [
            "Strong full-stack project background with relevant Python backend and React frontend experience.",
            "Clear metrics-driven bullet points demonstrating database optimization and API performance gains.",
            "Consistent exposure to modern version control and containerized developer workflows.",
            "Well-structured education and technical skills taxonomy recognized seamlessly by ATS parsers."
        ],
        "resume_improvements": [
            "Quantify business impact on production deployments rather than solely listing daily responsibilities.",
            "Explicitly highlight cloud infrastructure concepts (e.g., AWS ECS, S3, RDS) in your experience section.",
            "Consolidate redundant tool lists into distinct domain skill clusters for faster recruiter scanning.",
            "Add a concise 2-sentence Professional Summary tailored directly to Full-Stack Engineering roles."
        ],
        "skills_to_learn": [
            {
                "skill": "Kubernetes & Container Orchestration",
                "priority": SkillPriority.HIGH,
                "reason": "Crucial requirement mentioned multiple times in the JD for production workload deployment.",
                "resources": [
                    {"title": "Docker & Kubernetes: The Complete Guide", "type": "Course", "provider": "Udemy / KodeKloud"},
                    {"title": "Kubernetes Official Interactive Tutorials", "type": "Documentation", "provider": "kubernetes.io"}
                ]
            },
            {
                "skill": "AWS Cloud Architecture (ECS, RDS, S3)",
                "priority": SkillPriority.HIGH,
                "reason": "Core infrastructure environment required for the engineering team's current stack.",
                "resources": [
                    {"title": "AWS Certified Solutions Architect Associate Path", "type": "Certification", "provider": "Coursera / AWS Training"},
                    {"title": "AWS Well-Architected Framework Guide", "type": "Whitepaper", "provider": "Amazon Web Services"}
                ]
            },
            {
                "skill": "CI/CD Pipeline Automation",
                "priority": SkillPriority.MEDIUM,
                "reason": "Expected for automated testing, linting, and continuous delivery to staging.",
                "resources": [
                    {"title": "Automating Workflows with GitHub Actions", "type": "Tutorial", "provider": "GitHub Skills"}
                ]
            },
            {
                "skill": "Redis Caching & Session Management",
                "priority": SkillPriority.LOW,
                "reason": "Beneficial for high-throughput API endpoints and stateful caching layers.",
                "resources": [
                    {"title": "Redis University: RU101 Introduction to Redis Data Structures", "type": "Free Course", "provider": "Redis University"}
                ]
            }
        ]
    }


def get_mock_recruiter_candidates() -> List[Dict[str, Any]]:
    """Return mock candidate list for Recruiter batch screening and ranking."""
    return [
        {
            "id": "cand-01",
            "rank": 1,
            "name": "Alex Morgan",
            "filename": "Alex_Morgan_Senior_Engineer.pdf",
            "overall_match": 94,
            "skill_match": 96,
            "content_similarity": 92,
            "jd_coverage": 95,
            "experience_years": 5.5,
            "status": CandidateStatus.RECOMMENDED,
            "education": "B.S. in Computer Science, UC Berkeley (2020)",
            "summary": "Full-stack engineer with 5.5 years of experience building Python microservices, distributed PostgreSQL databases, and high-throughput React frontends on AWS.",
            "current_title": "Senior Software Engineer @ CloudScale Tech",
            "matched_skills": ["Python", "React", "PostgreSQL", "AWS", "Docker", "Kubernetes", "CI/CD", "TypeScript", "RESTful APIs", "Git"],
            "missing_skills": ["Redis", "GraphQL"],
            "requirements_satisfied": [
                "5+ years full stack engineering experience (exceeds 3+ yrs req)",
                "Deep proficiency in Python (FastAPI/Django) and React",
                "Extensive cloud infrastructure & container orchestration (AWS, Docker, K8s)",
                "Proven track record with SQL database schema design & performance tuning"
            ],
            "requirements_unsatisfied": [
                "No direct mention of Redis caching strategies in primary project summaries"
            ],
            "recommendation_note": "Strong Match — Candidate demonstrates comprehensive alignment across core tech stack, distributed architecture, and team leadership. Recommended for technical phone screen."
        },
        {
            "id": "cand-02",
            "rank": 2,
            "name": "Sophia Lin",
            "filename": "Sophia_Lin_Resume_2026.pdf",
            "overall_match": 89,
            "skill_match": 91,
            "content_similarity": 87,
            "jd_coverage": 90,
            "experience_years": 4.0,
            "status": CandidateStatus.RECOMMENDED,
            "education": "M.S. in Software Engineering, Carnegie Mellon (2022)",
            "summary": "Full stack engineer specializing in Python backends, React applications, and automated CI/CD deployment pipelines on AWS.",
            "current_title": "Software Engineer II @ DataVibe Labs",
            "matched_skills": ["Python", "React", "PostgreSQL", "AWS", "Docker", "CI/CD", "TypeScript", "RESTful APIs", "Git"],
            "missing_skills": ["Kubernetes", "Redis"],
            "requirements_satisfied": [
                "4 years full-stack development experience",
                "Strong mastery of Python, TypeScript, and React ecosystem",
                "Experience with Docker and GitHub Actions CI/CD workflows",
                "Hands-on PostgreSQL query optimization"
            ],
            "requirements_unsatisfied": [
                "Lacks direct Kubernetes cluster orchestration experience (uses AWS ECS)"
            ],
            "recommendation_note": "Strong Match — Strong academic and professional foundation with robust full-stack skill profile. Recommended for recruiter screening call."
        },
        {
            "id": "cand-03",
            "rank": 3,
            "name": "Marcus Vance",
            "filename": "Marcus_Vance_FullStack.docx",
            "overall_match": 82,
            "skill_match": 85,
            "content_similarity": 80,
            "jd_coverage": 83,
            "experience_years": 3.5,
            "status": CandidateStatus.REVIEW,
            "education": "B.S. in Information Systems, Univ of Washington (2022)",
            "summary": "Full Stack Developer proficient in Python web frameworks, React, and relational database systems with a focus on API design.",
            "current_title": "Full Stack Engineer @ AppSphere Solutions",
            "matched_skills": ["Python", "React", "PostgreSQL", "Docker", "RESTful APIs", "Git", "SQL"],
            "missing_skills": ["AWS", "Kubernetes", "CI/CD"],
            "requirements_satisfied": [
                "3.5 years of full stack web development",
                "Proficient with Python (Flask/Django) and React",
                "Solid foundation in database indexing and REST architecture"
            ],
            "requirements_unsatisfied": [
                "Limited public cloud (AWS/GCP) deployment experience; primarily on-prem/Heroku",
                "No formal CI/CD automation or Kubernetes exposure"
            ],
            "recommendation_note": "Moderate Match — Strong application development fundamentals; cloud and container orchestration gaps warrant a brief technical assessment."
        },
        {
            "id": "cand-04",
            "rank": 4,
            "name": "Elena Rostova",
            "filename": "Elena_Rostova_CV.pdf",
            "overall_match": 71,
            "skill_match": 74,
            "content_similarity": 68,
            "jd_coverage": 72,
            "experience_years": 2.0,
            "status": CandidateStatus.REVIEW,
            "education": "B.S. in Computer Science, Georgia Tech (2024)",
            "summary": "Junior-to-Mid full stack software engineer with core experience in Python, JavaScript, and PostgreSQL database queries.",
            "current_title": "Associate Software Engineer @ NextWave Digital",
            "matched_skills": ["Python", "JavaScript", "React", "SQL", "Git", "RESTful APIs"],
            "missing_skills": ["FastAPI", "Docker", "Kubernetes", "PostgreSQL", "AWS", "CI/CD"],
            "requirements_satisfied": [
                "Solid computer science fundamentals",
                "Experience building web applications with Python and React"
            ],
            "requirements_unsatisfied": [
                "Under 3 years of professional full-stack experience (2.0 years)",
                "No cloud infrastructure or container orchestration knowledge demonstrated"
            ],
            "recommendation_note": "Potential Match / Growth Candidate — Promising fundamentals but falls slightly below the senior experience threshold."
        },
        {
            "id": "cand-05",
            "rank": 5,
            "name": "Devon Brooks",
            "filename": "Devon_Brooks_Engineer.pdf",
            "overall_match": 58,
            "skill_match": 60,
            "content_similarity": 55,
            "jd_coverage": 62,
            "experience_years": 1.5,
            "status": CandidateStatus.LOW_MATCH,
            "education": "Full Stack Web Bootcamp Certification (2024)",
            "summary": "Frontend-oriented developer with foundational Python scripting skills and responsive web design background.",
            "current_title": "Junior Frontend Developer @ PixelCraft Studios",
            "matched_skills": ["JavaScript", "React", "Git", "HTML/CSS"],
            "missing_skills": ["Python", "PostgreSQL", "Docker", "Kubernetes", "AWS", "CI/CD", "FastAPI"],
            "requirements_satisfied": [
                "React frontend component architecture experience"
            ],
            "requirements_unsatisfied": [
                "Missing primary backend requirements (Python, PostgreSQL, API design)",
                "No DevOps, cloud, or orchestration experience"
            ],
            "recommendation_note": "Low Match — Significant gaps in backend architecture and cloud systems required for this senior position."
        }
    ]


def get_candidate_by_id(candidate_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full mock candidate profile and matching details by ID."""
    candidates = get_mock_recruiter_candidates()
    for c in candidates:
        if c["id"] == candidate_id:
            return c
    return candidates[0] if candidates else None
