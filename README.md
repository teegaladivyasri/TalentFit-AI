# TalentFit AI — AI Resume Screening & Career Matching Platform

A modern, production-grade web application designed to benchmark resumes against Job Descriptions for both **Job Seekers** and **Recruiters**.

---

## 🎯 Project Overview

**TalentFit AI** bridges the gap between candidates and hiring teams by translating complex job descriptions into clear, actionable career plans and standardized candidate rankings.

- **For Job Seekers:** Understand how well your resume matches target job postings, uncover missing critical competencies, receive prioritized learning paths, and optimize your application for Applicant Tracking Systems (ATS).
- **For Recruiters:** Screen candidates objectively, benchmark single applicants or multi-resume batches, explore interactive candidate matrices, and review automated recommendation advisories.

---

## 🚀 Current Status: Phase 5 — Final UI/UX Polish, Product Presentation & Release Readiness Complete

TalentFit AI is a fully polished, production-ready, SaaS-grade deterministic career matching and candidate screening platform. All operations are local, private, explainable, and visually refined, backed by **153 automated unit, integration, security, and performance regression tests**.

### Complete Pipeline Architecture

```text
Resume / JD Documents (PDF, DOCX, TXT, MD)
               │
               ▼
[Phase 2A: Document Parser] ── Multi-page extraction, filename sanitization, traceback privacy, 500k char bounds
               │
               ▼
[Phase 2B: Text Preprocessor] ── Unicode NFKC, technical term preservation, regex bounds safety
               │
               ▼
[Phase 2C: Skill Extractor] ── 93 canonical skills, alias mapping, boundary safety, evidence snippets
               │
               ▼
[Phase 2D: Resume Matcher & Scorer] ── Canonical comparison, 70/30 explainable scoring model
               │
               ├──> Matched Skills (with section attribution & occurrences)
               ├──> Missing Skills (with priority & evidence)
               ├──> Extra Skills (isolated from requirement denominator)
               ├──> Required Skills Coverage %
               ├──> TF-IDF + Cosine Content Similarity %
               └──> Composite Overall Match Score (0 - 100%)
               │
               ▼
[Phase 2E: ATS Analyzer & Recommender] ── Parse readiness & career guidance
               │
               ├──> 5-Component ATS Compatibility Score (0 - 100%)
               ├──> Prioritized Skill Gaps (HIGH / MEDIUM / LOW)
               ├──> Actionable Evidence-Based Resume Improvements
               ├──> Curated Skill Learning Roadmap with Focus Areas
               └──> Situational Guidance Headline & Advisory
               │
               ▼
[Phase 2F: Quality Hardening & Validation] ── Stress-tested against 10 synthetic archetypes
               │
               ▼
[Phase 3: Recruiter Screening & Comparison] ── Real batch ranking, multi-faceted filtering, candidate details, comparison matrix
               │
               ▼
[Phase 4: Security & Deployment Hardening] ── Input sanitization, memory safety, 100-candidate scaling (sub-second)
               │
               ▼
[Phase 5: SaaS UI/UX Polish & Release Readiness] ── SaaS design system, high-contrast light/dark themes, interactive hero preview, 4 KPI cards (153/153 tests passing)
```

---

## 🔒 Security & Privacy Guarantees

- **Supported Upload Formats:** `.pdf`, `.docx`, `.txt`, `.md`
- **File Size Limit:** $10\text{ MB}$ maximum upload size with automatic rejection of 0-byte files.
- **Malformed Document Protection:** Corrupted or password-protected files fail with user-friendly notices without exposing stack traces, server filepaths, or module internals.
- **Path Traversal Sanitization:** All uploaded filenames are stripped of directory traversal sequences (`../`, `..\`, `/etc/`).
- **No Code Execution:** Zero evaluation (`eval`, `exec`, `pickle`, `subprocess`) of uploaded file bytes.
- **Zero Sensitive Data Logging:** Candidate PII and raw resume text are never logged or dumped to console output.
- **Session-Based Privacy:** Resumes are processed in memory and never stored in a persistent database.

---

## 📐 Explainable Scoring & Guidance Models

The matching and guidance systems avoid arbitrary multipliers or opaque black-box percentages. All scores are derived from mathematical formulas:

### 1. Overall Composite Compatibility Score (70% / 30%)
$$\text{Overall Score} = \text{round}\Big(0.70 \times \text{Skill Match Score} + 0.30 \times \text{Content Similarity Score}\Big)$$

### 2. Skill Match Score (Weighted by Requirement Level)
$$\text{Skill Match Score} = \left( \frac{\sum \text{Weight of Matched JD Skills}}{\sum \text{Weight of All JD Skills}} \right) \times 100$$
- **Required Skill Weight:** $1.0$ (identified from requirements sections or mandatory phrasing)
- **Preferred Skill Weight:** $0.5$ (identified from bonus/preferred qualifications)
- **Extra Resume Skills:** Displayed transparently to recruiters/candidates, but do **not** artificially inflate or dilute the JD denominator.

### 3. Required Skills Coverage
$$\text{Required Skills Coverage} = \left( \frac{\text{Matched Required Skills}}{\text{Total Required Skills}} \right) \times 100$$

### 4. ATS Compatibility Indicator (5-Component Weighted Heuristics)
$$\text{ATS Score} = \text{round}\Big(0.25 \times E + 0.25 \times S + 0.15 \times C + 0.20 \times V + 0.15 \times O\Big)$$
- **Text Extractability ($E$, 25%):** Word count, character density, and absence of extraction corruption.
- **Section Structure ($S$, 25%):** Detection of standard headers (`Skills`, `Experience`, `Education`, `Summary`, `Projects`).
- **Contact Information ($C$, 15%):** Direct regex detection of Email, Phone Number, and Online Links.
- **Skill Visibility ($V$, 20%):** Consolidation of skills in dedicated Skills and Experience sections.
- **Content Organization ($O$, 15%):** Balanced line lengths, bullet formatting, and absence of dense unbroken paragraphs.

> [!NOTE]
> The ATS compatibility score is a **project-defined parse-readiness indicator**, not a universal proprietary ATS company score.

### 5. Skill Gap Prioritization Rules
- **HIGH Priority:** Required JD skills missing from the candidate resume.
- **MEDIUM Priority:** Preferred / bonus JD skills missing from the resume.
- **LOW Priority:** Peripheral competencies mentioned in the role posting.
- **Ethical Wording:** Missing skills are framed as *"Not detected in resume"* rather than assuming the candidate lacks knowledge. Never recommends fabricating experience.

---

## 🛠️ Technology Stack

- **Frontend & Web Framework:** [Streamlit](https://streamlit.io/) (Modular Python architecture)
- **Styling & Design System:** Custom Vanilla CSS (Design Tokens, Light/Dark theme switching, Inter font stack)
- **Document Processing:** PyPDF, python-docx
- **NLP & Text Preprocessing:** Regex boundary engine, Unicode NFKC, safe stopword filtering
- **Information Retrieval & Machine Learning:** Scikit-Learn (TF-IDF Vectorization, Cosine Similarity)
- **Knowledge Base:** Curated JSON taxonomy (93 skills) and learning paths database
- **Data & Testing:** Pandas, Pytest (148 automated unit, integration, security & performance tests)

---

## 📁 Project Architecture

```text
AI Resume Screening/
├── app.py                      # Main entrypoint and page router
├── .streamlit/
│   └── config.toml             # Streamlit theme & server configuration
├── assets/
│   └── style.css               # Clean SaaS design system stylesheet (Light & Dark tokens)
├── components/
│   ├── navbar.py               # Top navigation bar with active route & theme toggle
│   ├── cards.py                # Stat cards, skill badges, callouts, hero preview
│   ├── upload.py               # Reusable file uploader with status badges
│   ├── score.py                # Visual score bars, gauges, ATS breakdown
│   ├── tables.py               # Recruiter ranking table & comparison matrix
│   └── theme.py                # Theme state management and CSS injector
├── pages/
│   ├── home.py                 # Landing page (Hero, workflow, persona selector)
│   ├── job_seeker.py           # Job seeker resume & JD upload, parsing & match analysis
│   ├── candidate_analysis.py   # Job seeker match results, guidance headline, skills gap & learning plan
│   ├── recruiter.py            # Recruiter hub (Single & Batch screening workflows)
│   ├── recruiter_screening.py  # Recruiter batch results, KPI cards, filter bar & ranked table
│   ├── candidate_details.py    # In-depth candidate evaluation report & 70/30 score breakdown
│   └── comparison.py           # Side-by-side candidate comparison matrix (2 to 4 candidates)
├── services/
│   ├── document_parser.py      # Multi-format document parser, name extractor & traversal sanitization
│   ├── text_preprocessor.py    # NLP text normalization, tokenization, section parser & size bounds
│   ├── skill_extractor.py      # Production skill extraction engine with alias mapping
│   ├── matcher.py              # Canonical skill matching & TF-IDF similarity engine
│   ├── scorer.py               # 70/30 Explainable scoring model & breakdown
│   ├── ats_analyzer.py         # 5-component deterministic ATS parse-readiness analyzer
│   └── recommender.py          # Skill gap prioritization & personalized learning roadmap engine
├── data/
│   ├── mock_data.py            # Reference datasets for Job Seeker and Recruiter
│   └── skills/
│       ├── skills_taxonomy.json # Multi-category skill taxonomy (93 canonical skills)
│       ├── learning_paths.json # Curated learning focus areas for canonical skills
│       └── sample_skills.json  # Fallback skill dictionary categorized by domain
├── utils/
│   ├── constants.py            # Route names, file constraints, status tags, config
│   ├── session_state.py        # Centralized state initialization, getters, setters, navigation
│   └── validators.py           # File extension, size, empty/0-byte input validation
├── tests/
│   ├── fixtures/
│   │   ├── synthetic_resumes.py   # Synthetic resumes A-J and JDs 1-3
│   │   └── benchmark_pipeline.py  # Latency and throughput benchmark script (1-100 batch)
│   ├── test_security_hardening.py # File validation, 0-byte, traceback privacy, isolation
│   ├── test_performance_regression.py # Workload scaling benchmarks (1, 10, 25, 50, 100)
│   ├── test_recruiter_screening.py # Batch screening, ranking, tie-breaking, search & filters
│   ├── test_candidate_comparison.py # Side-by-side candidate comparison matrix tests
│   ├── test_integration_pipeline.py # End-to-end integration & validation suite
│   ├── test_document_parser.py # Document parsing & file handling unit tests
│   ├── test_text_preprocessor.py # NLP cleaning, tokenization, section extraction tests
│   ├── test_skill_extractor.py # Skill extraction, aliases, false-positive protection tests
│   ├── test_matcher.py         # Matching, weighting, TF-IDF, scoring & ranking tests
│   ├── test_ats_analyzer.py    # ATS compatibility, contact info, structure & visibility tests
│   ├── test_recommender.py     # Skill gaps, suggestions, roadmaps & end-to-end pipeline tests
│   ├── test_validators.py      # Upload validation and text checks tests
│   ├── test_session_state.py   # State transitions and constants tests
│   └── test_services_stub.py   # Service contracts & mock data consistency tests
├── docs/
│   ├── validation_report.md               # Phase 2F validation & audit report
│   ├── recruiter_screening_validation.md # Phase 3 recruiter screening & comparison validation report
│   └── security_deployment_report.md     # Phase 4 security, performance & deployment report
├── requirements.txt            # Project dependencies
└── README.md                   # Comprehensive documentation
```

---

## ⚡ Installation & Running the Application

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.11/3.13)
- Git

### 2. Setup Virtual Environment
```bash
# Clone the repository
git clone <repo-url>
cd "AI Resume Screening"

# Create a virtual environment (optional but recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Running Unit Tests & Benchmarks

Run the complete test suite:
```bash
python -m pytest tests/ -v
```

Run the pipeline performance benchmark:
```bash
python tests/fixtures/benchmark_pipeline.py
```

---

## 🗺️ Project Roadmap

- [x] **Phase 1: Project Foundation & Professional UI**
- [x] **Phase 2A: Document Text Extraction**
- [x] **Phase 2B: NLP Text Preprocessing**
- [x] **Phase 2C: Skill Extraction Engine**
- [x] **Phase 2D: Resume-JD Matching & Explainable Scoring**
- [x] **Phase 2E: ATS Analysis, Skill Gap Prioritization & Career Guidance**
- [x] **Phase 2F: Real-World Validation & Quality Hardening** (Completed - 119 tests passing)
- [x] **Phase 3: Advanced Recruiter Screening & Candidate Comparison** (Completed - 133 tests passing)
- [x] **Phase 4: Security, Performance & Deployment Hardening** (Completed - 148 tests passing)

