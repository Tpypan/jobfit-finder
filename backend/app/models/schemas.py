"""Pydantic schemas for data models."""

from pydantic import BaseModel, Field


class ResumeProfile(BaseModel):
    """Structured profile extracted from a resume."""
    
    skills: list[str] = Field(default_factory=list, description="Technical and soft skills")
    experience: list[str] = Field(default_factory=list, description="Work experience bullets")
    education: list[str] = Field(default_factory=list, description="Education entries")
    keywords: list[str] = Field(default_factory=list, description="Key terms and technologies")


class JobPosting(BaseModel):
    """A job posting from a company careers page."""
    
    id: str = Field(description="Unique job identifier")
    title: str = Field(description="Job title")
    location: str = Field(default="", description="Job location")
    description: str = Field(default="", description="Full job description")
    apply_url: str = Field(description="Direct application URL")
    source: str = Field(description="Source platform (greenhouse, lever)")


class JobRequirements(BaseModel):
    """Structured requirements extracted from a job description."""
    
    must_have: list[str] = Field(default_factory=list, description="Required skills/qualifications")
    nice_to_have: list[str] = Field(default_factory=list, description="Preferred but not required")
    responsibilities: list[str] = Field(default_factory=list, description="Key job responsibilities")
    role_family: str = Field(default="", description="Role category (engineering, data, design, etc)")
    keywords: list[str] = Field(default_factory=list, description="Key terms from the posting")


class MatchResult(BaseModel):
    """Result of matching a job to a resume."""
    
    job: JobPosting = Field(description="The matched job posting")
    match_score: int = Field(ge=0, le=100, description="Match score from 0-100")
    why_matches: list[str] = Field(default_factory=list, description="Reasons for match (3-6 items)")
    gaps: list[str] = Field(default_factory=list, description="Potential gaps (1-5 items)")
