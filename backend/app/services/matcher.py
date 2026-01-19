"""Matcher service - orchestrates the full matching pipeline."""

import asyncio
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

from app.core.config import get_settings
from app.models.schemas import ResumeProfile, JobPosting, JobRequirements, MatchResult
from app.services.resume_parser import parse_resume
from app.services.job_sources.router import get_connector_for_url
from app.services.job_parser import parse_job_requirements
from app.services.scoring import (
    compute_match_score,
    generate_match_reasons,
    generate_gap_reasons,
)

logger = logging.getLogger(__name__)

# Simple file-based cache
CACHE_DIR = Path(__file__).parent.parent.parent / ".cache"


def get_cache_key(url: str) -> str:
    """Generate cache key from URL."""
    return hashlib.md5(url.encode()).hexdigest()


def load_cached_jobs(url: str) -> list[dict] | None:
    """Load cached jobs if still valid."""
    settings = get_settings()
    cache_key = get_cache_key(url)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    if not cache_file.exists():
        return None
    
    try:
        data = json.loads(cache_file.read_text())
        cached_at = datetime.fromisoformat(data["cached_at"])
        ttl = timedelta(minutes=settings.job_cache_ttl_minutes)
        
        if datetime.now() - cached_at < ttl:
            logger.info(f"Using cached jobs for {url}")
            return data["jobs"]
    except Exception as e:
        logger.warning(f"Failed to load cache: {e}")
    
    return None


def save_jobs_to_cache(url: str, jobs: list[JobPosting]) -> None:
    """Save jobs to cache."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_key = get_cache_key(url)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    data = {
        "cached_at": datetime.now().isoformat(),
        "url": url,
        "jobs": [job.model_dump() for job in jobs],
    }
    
    cache_file.write_text(json.dumps(data, indent=2))
    logger.info(f"Cached {len(jobs)} jobs for {url}")


async def match_jobs(
    resume_text: str | None = None,
    resume_file_base64: str | None = None,
    desired_job_description: str = "",
    company_jobs_url: str = "",
) -> list[MatchResult]:
    """
    Full matching pipeline.
    
    Args:
        resume_text: Plain text resume
        resume_file_base64: Base64 encoded PDF/DOCX
        desired_job_description: User's desired job types
        company_jobs_url: URL to company's job board
        
    Returns:
        List of MatchResult sorted by score descending
    """
    settings = get_settings()
    
    # Step 1: Parse resume
    logger.info("Parsing resume...")
    resume_profile = await parse_resume(
        resume_text=resume_text,
        resume_file_base64=resume_file_base64,
    )
    
    # Step 2: Fetch jobs (with caching)
    logger.info(f"Fetching jobs from {company_jobs_url}...")
    cached = load_cached_jobs(company_jobs_url)
    
    if cached:
        jobs = [JobPosting.model_validate(j) for j in cached]
    else:
        connector = get_connector_for_url(company_jobs_url)
        jobs = await connector.fetch_jobs(max_jobs=settings.max_jobs_fetch)
        save_jobs_to_cache(company_jobs_url, jobs)
    
    if not jobs:
        logger.warning("No jobs found")
        return []
    
    logger.info(f"Processing {len(jobs)} jobs...")
    
    # Step 3: Extract requirements and score each job
    results: list[MatchResult] = []
    
    # Process jobs concurrently in batches
    batch_size = 10
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        
        # Parse requirements concurrently
        requirement_tasks = [parse_job_requirements(job) for job in batch]
        requirements_list = await asyncio.gather(*requirement_tasks, return_exceptions=True)
        
        for job, requirements in zip(batch, requirements_list):
            if isinstance(requirements, Exception):
                logger.warning(f"Failed to parse requirements for {job.title}: {requirements}")
                requirements = JobRequirements(role_family="other")
            
            # Compute score
            score_breakdown = compute_match_score(
                resume_profile=resume_profile,
                job_requirements=requirements,
                desired_description=desired_job_description,
            )
            
            # Generate explanations
            why_matches = generate_match_reasons(
                resume_profile=resume_profile,
                job_requirements=requirements,
                score_breakdown=score_breakdown,
            )
            
            gaps = generate_gap_reasons(
                resume_profile=resume_profile,
                job_requirements=requirements,
            )
            
            results.append(MatchResult(
                job=job,
                match_score=score_breakdown.final_score,
                why_matches=why_matches,
                gaps=gaps,
            ))
    
    # Sort by score descending and return top 10
    results.sort(key=lambda r: r.match_score, reverse=True)
    
    logger.info(f"Returning top {min(10, len(results))} matches")
    return results[:10]
