"""Greenhouse job board connector."""

import re
import logging
from urllib.parse import urlparse

import httpx

from app.models.schemas import JobPosting
from app.services.job_sources.base import JobSourceConnector

logger = logging.getLogger(__name__)


class GreenhouseConnector(JobSourceConnector):
    """Connector for Greenhouse job boards (boards.greenhouse.io)."""
    
    source_name = "greenhouse"
    
    def __init__(self, company_url: str):
        super().__init__(company_url)
        self.company_slug = self._extract_company_slug()
        self.api_base = f"https://boards-api.greenhouse.io/v1/boards/{self.company_slug}"
    
    def _extract_company_slug(self) -> str:
        """Extract company slug from URL like boards.greenhouse.io/companyname."""
        parsed = urlparse(self.company_url)
        path_parts = [p for p in parsed.path.split("/") if p]
        
        if not path_parts:
            raise ValueError(f"Could not extract company from URL: {self.company_url}")
        
        return path_parts[0]
    
    async def fetch_jobs(self, max_jobs: int = 200) -> list[JobPosting]:
        """Fetch jobs from Greenhouse API."""
        jobs = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Fetch all jobs with content
                response = await client.get(
                    f"{self.api_base}/jobs",
                    params={"content": "true"}
                )
                response.raise_for_status()
                data = response.json()
                
                for job_data in data.get("jobs", [])[:max_jobs]:
                    # Clean HTML from description
                    description = job_data.get("content", "")
                    description = self._clean_html(description)
                    
                    # Get location
                    location = job_data.get("location", {}).get("name", "")
                    
                    jobs.append(JobPosting(
                        id=str(job_data["id"]),
                        title=job_data.get("title", ""),
                        location=location,
                        description=description,
                        apply_url=job_data.get("absolute_url", ""),
                        source=self.source_name,
                    ))
                
                logger.info(f"Fetched {len(jobs)} jobs from Greenhouse ({self.company_slug})")
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch Greenhouse jobs: {e}")
                raise ValueError(f"Could not fetch jobs from Greenhouse: {e}")
        
        return jobs
    
    async def fetch_job_details(self, job_id: str) -> str:
        """Fetch detailed job description."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.api_base}/jobs/{job_id}")
            response.raise_for_status()
            data = response.json()
            return self._clean_html(data.get("content", ""))
    
    @staticmethod
    def _clean_html(html: str) -> str:
        """Remove HTML tags from content."""
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', ' ', html)
        # Normalize whitespace
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
