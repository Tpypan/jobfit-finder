"""Base class for job source connectors."""

from abc import ABC, abstractmethod

from app.models.schemas import JobPosting


class JobSourceConnector(ABC):
    """Abstract base class for job source connectors."""
    
    source_name: str = "unknown"
    
    def __init__(self, company_url: str):
        """
        Initialize connector with company jobs URL.
        
        Args:
            company_url: The company's careers/jobs page URL
        """
        self.company_url = company_url
    
    @abstractmethod
    async def fetch_jobs(self, max_jobs: int = 200) -> list[JobPosting]:
        """
        Fetch job postings from the source.
        
        Args:
            max_jobs: Maximum number of jobs to fetch
            
        Returns:
            List of JobPosting objects
        """
        pass
    
    @abstractmethod
    async def fetch_job_details(self, job_id: str) -> str:
        """
        Fetch detailed job description for a specific job.
        
        Args:
            job_id: The job identifier
            
        Returns:
            Job description text
        """
        pass
