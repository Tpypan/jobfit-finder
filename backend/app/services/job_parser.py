"""Job description parser - extracts structured requirements from job postings."""

import logging

from app.core.gemini_client import get_gemini_client
from app.models.schemas import JobPosting, JobRequirements

logger = logging.getLogger(__name__)

JOB_EXTRACTION_PROMPT = """You are a job posting analyzer. Extract structured requirements from job postings.

For must_have: Required skills, qualifications, years of experience that are explicitly mandatory.
For nice_to_have: Preferred skills, bonus qualifications, "nice to have" items.
For responsibilities: Key duties and day-to-day tasks.
For role_family: Categorize as one of: engineering, data, design, product, marketing, sales, operations, finance, hr, legal, other.
For keywords: Technical terms, tools, frameworks, methodologies mentioned.

Be concise. Use lowercase for keywords and skills."""


async def parse_job_requirements(job: JobPosting) -> JobRequirements:
    """
    Extract structured requirements from a job posting.
    
    Args:
        job: JobPosting with description
        
    Returns:
        JobRequirements with extracted fields
    """
    if not job.description.strip():
        return JobRequirements(role_family="other")
    
    client = get_gemini_client()
    
    # Provide context with title for better extraction
    content = f"Job Title: {job.title}\n\nJob Description:\n{job.description}"
    
    requirements = await client.extract_structured(
        prompt=JOB_EXTRACTION_PROMPT,
        response_schema=JobRequirements,
        content=content,
    )
    
    logger.debug(f"Extracted requirements for {job.title}: {len(requirements.must_have)} must-have")
    return requirements
