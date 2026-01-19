"""Lever job board connector."""

import re
import logging
from urllib.parse import urlparse

import httpx

from app.models.schemas import JobPosting
from app.services.job_sources.base import JobSourceConnector

logger = logging.getLogger(__name__)


class LeverConnector(JobSourceConnector):
    """Connector for Lever job boards (jobs.lever.co)."""
    
    source_name = "lever"
    
    def __init__(self, company_url: str):
        super().__init__(company_url)
        self.company_slug = self._extract_company_slug()
        self.api_base = f"https://api.lever.co/v0/postings/{self.company_slug}"
    
    def _extract_company_slug(self) -> str:
        """Extract company slug from URL like jobs.lever.co/companyname."""
        parsed = urlparse(self.company_url)
        path_parts = [p for p in parsed.path.split("/") if p]
        
        if not path_parts:
            raise ValueError(f"Could not extract company from URL: {self.company_url}")
        
        return path_parts[0]
    
    async def fetch_jobs(self, max_jobs: int = 200) -> list[JobPosting]:
        """Fetch jobs from Lever API."""
        jobs = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(self.api_base)
                response.raise_for_status()
                data = response.json()
                
                for job_data in data[:max_jobs]:
                    # Get description from various possible fields
                    description_parts = []
                    
                    if job_data.get("descriptionPlain"):
                        description_parts.append(job_data["descriptionPlain"])
                    
                    # Add lists content
                    for item in job_data.get("lists", []):
                        if item.get("text"):
                            description_parts.append(item["text"])
                        if item.get("content"):
                            description_parts.append(self._clean_html(item["content"]))
                    
                    # Additional info
                    if job_data.get("additionalPlain"):
                        description_parts.append(job_data["additionalPlain"])
                    
                    description = "\n\n".join(description_parts)
                    
                    # Build location string
                    location = job_data.get("workplaceType", "")
                    if job_data.get("categories", {}).get("location"):
                        location = job_data["categories"]["location"]
                    
                    jobs.append(JobPosting(
                        id=job_data["id"],
                        title=job_data.get("text", ""),
                        location=location,
                        description=description,
                        apply_url=job_data.get("applyUrl", job_data.get("hostedUrl", "")),
                        source=self.source_name,
                    ))
                
                logger.info(f"Fetched {len(jobs)} jobs from Lever ({self.company_slug})")
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch Lever jobs: {e}")
                raise ValueError(f"Could not fetch jobs from Lever: {e}")
        
        return jobs
    
    async def fetch_job_details(self, job_id: str) -> str:
        """Fetch detailed job description."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.api_base}/{job_id}")
            response.raise_for_status()
            data = response.json()
            
            parts = []
            if data.get("descriptionPlain"):
                parts.append(data["descriptionPlain"])
            for item in data.get("lists", []):
                if item.get("text"):
                    parts.append(item["text"])
                if item.get("content"):
                    parts.append(self._clean_html(item["content"]))
            
            return "\n\n".join(parts)
    
    @staticmethod
    def _clean_html(html: str) -> str:
        """Remove HTML tags from content."""
        clean = re.sub(r'<[^>]+>', ' ', html)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
