"""Pipeline Performance Benchmark Script.

Measures the latency and throughput of the complete end-to-end TalentFit AI pipeline:
Text Preprocessing -> Skill Extraction -> Matching -> Scoring -> ATS Analysis -> Recommendations -> Learning Roadmap
for batches of 1, 10, 25, 50, and 100 candidate resumes against a Job Description.
"""

import time
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.text_preprocessor import TextPreprocessor
from services.skill_extractor import SkillExtractor
from services.matcher import ResumeMatcher
from services.scorer import ScorerService
from services.ats_analyzer import ATSAnalyzer
from services.recommender import RecommendationService
from tests.fixtures.synthetic_resumes import (
    RESUME_A_STRONG_MATCH,
    RESUME_B_MODERATE_MATCH,
    RESUME_C_WEAK_MATCH,
    RESUME_D_EXTRA_SKILLS,
    RESUME_E_ALIAS_HEAVY,
    JD_1_PYTHON_BACKEND
)


def run_benchmark():
    preprocessor = TextPreprocessor()
    extractor = SkillExtractor()
    scorer = ScorerService()
    matcher = ResumeMatcher(scorer=scorer)
    ats_analyzer = ATSAnalyzer()
    recommender = RecommendationService(ats_analyzer=ats_analyzer)

    sample_pool = [
        RESUME_A_STRONG_MATCH,
        RESUME_B_MODERATE_MATCH,
        RESUME_C_WEAK_MATCH,
        RESUME_D_EXTRA_SKILLS,
        RESUME_E_ALIAS_HEAVY
    ]

    jd_text = JD_1_PYTHON_BACKEND

    # Warmup
    jd_proc = preprocessor.preprocess(jd_text, doc_type="jd")
    jd_skills = extractor.extract(text=jd_proc["normalized_text"], sections=jd_proc["sections"])

    batch_sizes = [1, 10, 25, 50, 100]
    results = {}

    print("=" * 70)
    print("TalentFit AI — End-to-End Pipeline Performance Benchmark (Phase 4)")
    print("=" * 70)

    for size in batch_sizes:
        resumes_batch = [sample_pool[i % len(sample_pool)] for i in range(size)]
        
        start_time = time.perf_counter()
        
        # Process JD once per batch (standard recruiter workflow)
        j_proc = preprocessor.preprocess(jd_text, doc_type="jd")
        j_skills = extractor.extract(text=j_proc["normalized_text"], sections=j_proc["sections"])
        
        for resume_text in resumes_batch:
            # 1. Preprocess
            r_proc = preprocessor.preprocess(resume_text, doc_type="resume", remove_stopwords=True)
            # 2. Skill Extraction
            r_skills = extractor.extract(text=r_proc["normalized_text"], sections=r_proc["sections"])
            # 3. Matching & Scoring
            match_res = matcher.match(
                resume_skills=r_skills,
                jd_skills=j_skills,
                resume_text=r_proc["cleaned_text"],
                jd_text=j_proc["cleaned_text"]
            )
            # 4. ATS Parse-Readiness
            ats_res = ats_analyzer.analyze(
                resume_text=r_proc["normalized_text"],
                resume_processed=r_proc,
                resume_skills=r_skills
            )
            # 5. Career Guidance & Recommender
            guidance_res = recommender.generate(
                match_result=match_res,
                resume_processed=r_proc,
                resume_skills=r_skills,
                jd_processed=j_proc,
                jd_skills=j_skills,
                ats_result=ats_res
            )

        elapsed = time.perf_counter() - start_time
        avg_per_resume = (elapsed / size) * 1000  # in ms
        
        results[size] = {
            "total_seconds": elapsed,
            "avg_ms_per_resume": avg_per_resume
        }
        
        print(f"Candidates: {size:3d} | Total Time: {elapsed:6.3f}s | Avg / Candidate: {avg_per_resume:6.2f} ms")

    print("=" * 70)
    print("Benchmark complete.")
    return results


if __name__ == "__main__":
    run_benchmark()
