"""API routes for JobFit Finder."""

import logging

from fastapi import APIRouter, HTTPException

from app.api.types import RecommendRequest, RecommendResponse, ErrorResponse
from app.services.matcher import match_jobs
from app.services.job_sources.router import UnsupportedJobSourceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def recommend_jobs(request: RecommendRequest) -> RecommendResponse:
    """
    Get job recommendations based on resume and preferences.
    
    Upload a resume (text or PDF/DOCX), describe your desired job,
    and provide a company jobs URL to get matched recommendations.
    """
    # Validate resume input
    if not request.resume_text and not request.resume_file_base64:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "MissingResume",
                "message": "Either resume_text or resume_file_base64 must be provided",
            },
        )
    
    try:
        results = await match_jobs(
            resume_text=request.resume_text,
            resume_file_base64=request.resume_file_base64,
            desired_job_description=request.desired_job_description,
            company_jobs_url=request.company_jobs_url,
        )
        
        return RecommendResponse(results=results)
    
    except UnsupportedJobSourceError as e:
        logger.warning(f"Unsupported job source: {e.url}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "UnsupportedURL",
                "message": str(e),
            },
        )
    
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "message": str(e),
            },
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error in recommend_jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ServerError",
                "message": "An unexpected error occurred. Please try again.",
            },
        )
