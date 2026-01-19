"""API request and response types."""

from pydantic import BaseModel, Field

from app.models.schemas import MatchResult


class RecommendRequest(BaseModel):
    """Request body for /api/recommend endpoint."""
    
    resume_text: str | None = Field(
        default=None,
        description="Plain text resume content"
    )
    resume_file_base64: str | None = Field(
        default=None,
        description="Base64-encoded PDF or DOCX resume file"
    )
    desired_job_description: str = Field(
        description="User's description of desired job types",
        examples=["data analyst intern, SQL, remote", "software engineer, backend, Python"]
    )
    company_jobs_url: str = Field(
        description="URL to company's job board (Greenhouse or Lever)",
        examples=["https://boards.greenhouse.io/stripe", "https://jobs.lever.co/figma"]
    )


class RecommendResponse(BaseModel):
    """Response body for /api/recommend endpoint."""
    
    results: list[MatchResult] = Field(
        description="Top job matches sorted by score descending"
    )


class ErrorResponse(BaseModel):
    """Error response body."""
    
    error: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
