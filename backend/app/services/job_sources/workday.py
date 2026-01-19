"""Workday job board connector."""

import re
import logging
from urllib.parse import urlparse

import httpx

from app.models.schemas import JobPosting
from app.services.job_sources.base import JobSourceConnector

logger = logging.getLogger(__name__)


class WorkdayConnector(JobSourceConnector):
    """Connector for Workday job boards (*.myworkdayjobs.com)."""
    
    source_name = "workday"
    
    def __init__(self, company_url: str):
        super().__init__(company_url)
        self.company_slug, self.site_slug = self._extract_slugs()
        # Workday uses a CXS API endpoint for job data
        # Note: api_base must use self.wd_instance which is set during _extract_slugs()
        self.api_base = f"https://{self.company_slug}.{self.wd_instance}.myworkdayjobs.com/wday/cxs/{self.company_slug}/{self.site_slug}"
    
    def _extract_slugs(self) -> tuple[str, str]:
        """
        Extract company and site slugs from URL.
        
        URL patterns:
        - https://company.wd5.myworkdayjobs.com/en-US/External
        - https://company.wd1.myworkdayjobs.com/careers
        """
        parsed = urlparse(self.company_url)
        host = parsed.netloc
        
        # Extract company from subdomain (e.g., "nvidia" from "nvidia.wd5.myworkdayjobs.com")
        company_slug = host.split(".")[0]
        
        # Extract site from path (e.g., "External" from "/en-US/External")
        path_parts = [p for p in parsed.path.split("/") if p and p not in ("en-US", "en", "de", "fr", "es", "ja", "zh")]
        site_slug = path_parts[0] if path_parts else "External"
        
        # Detect which Workday instance (wd1, wd5, etc.)
        wd_instance = "wd5"  # default
        for part in host.split("."):
            if part.startswith("wd") and part[2:].isdigit():
                wd_instance = part
                break
        
        # Update API base with correct instance
        self.wd_instance = wd_instance
        
        return company_slug, site_slug
    
    async def fetch_jobs(self, max_jobs: int = 200) -> list[JobPosting]:
        """Fetch jobs from Workday API."""
        jobs = []
        offset = 0
        limit = 20  # Workday typically returns 20 per page
        
        # Reconstruct API base with correct Workday instance
        api_base = f"https://{self.company_slug}.{self.wd_instance}.myworkdayjobs.com/wday/cxs/{self.company_slug}/{self.site_slug}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                while len(jobs) < max_jobs:
                    # Workday uses POST requests with JSON body for job searches
                    response = await client.post(
                        f"{api_base}/jobs",
                        json={
                            "appliedFacets": {},
                            "limit": limit,
                            "offset": offset,
                            "searchText": "",
                        },
                        headers={
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    job_postings = data.get("jobPostings", [])
                    if not job_postings:
                        break
                    
                    for job_data in job_postings:
                        if len(jobs) >= max_jobs:
                            break
                        
                        # Get job details URL
                        external_path = job_data.get("externalPath", "")
                        job_url = f"https://{self.company_slug}.{self.wd_instance}.myworkdayjobs.com{external_path}"
                        
                        # Get location - may be in different fields
                        location = job_data.get("locationsText", "")
                        if not location:
                            locations = job_data.get("bulletFields", [])
                            location = locations[0] if locations else ""
                        
                        jobs.append(JobPosting(
                            id=job_data.get("bulletFields", [""])[0] if job_data.get("bulletFields") else str(offset + len(jobs)),
                            title=job_data.get("title", ""),
                            location=location,
                            description=job_data.get("descriptionTeaser", ""),
                            apply_url=job_url,
                            source=self.source_name,
                        ))
                    
                    offset += limit
                    
                    # Check if we've fetched all available jobs
                    total = data.get("total", 0)
                    if offset >= total:
                        break
                
                # Fetch full descriptions for each job (batch of first 50 for performance)
                jobs = await self._enrich_job_descriptions(client, jobs[:min(50, len(jobs))], api_base)
                
                logger.info(f"Fetched {len(jobs)} jobs from Workday ({self.company_slug}/{self.site_slug})")
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch Workday jobs: {e}")
                raise ValueError(f"Could not fetch jobs from Workday: {e}")
        
        return jobs
    
    async def _enrich_job_descriptions(
        self, 
        client: httpx.AsyncClient, 
        jobs: list[JobPosting],
        api_base: str,
    ) -> list[JobPosting]:
        """Fetch full job descriptions for each job."""
        enriched = []
        
        for job in jobs:
            try:
                # Extract job path from URL
                parsed = urlparse(job.apply_url)
                job_path = parsed.path
                
                response = await client.get(
                    f"{api_base}{job_path}",
                    headers={"Accept": "application/json"},
                )
                
                if response.status_code == 200:
                    data = response.json()
                    job_detail = data.get("jobPostingInfo", {})
                    
                    # Get full description
                    description = job_detail.get("jobDescription", job.description)
                    description = self._clean_html(description)
                    
                    # Update location if available
                    location = job_detail.get("location", job.location)
                    
                    enriched.append(JobPosting(
                        id=job.id,
                        title=job_detail.get("title", job.title),
                        location=location,
                        description=description,
                        apply_url=job.apply_url,
                        source=job.source,
                    ))
                else:
                    enriched.append(job)
                    
            except Exception as e:
                logger.warning(f"Failed to enrich job {job.title}: {e}")
                enriched.append(job)
        
        return enriched
    
    async def fetch_job_details(self, job_id: str) -> str:
        """Fetch detailed job description."""
        # Job details are fetched during listing enrichment
        return ""
    
    @staticmethod
    def _clean_html(html: str) -> str:
        """Remove HTML tags from content."""
        if not html:
            return ""
        clean = re.sub(r'<[^>]+>', ' ', html)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
