"""Router for selecting appropriate job source connector based on URL."""

import re
from urllib.parse import urlparse

from app.services.job_sources.base import JobSourceConnector
from app.services.job_sources.greenhouse import GreenhouseConnector
from app.services.job_sources.lever import LeverConnector


class UnsupportedJobSourceError(Exception):
    """Raised when the job source URL is not supported."""
    
    def __init__(self, url: str):
        self.url = url
        super().__init__(
            f"Unsupported jobs link: {url}. "
            "Currently supports: Greenhouse (https://boards.greenhouse.io/...) "
            "and Lever (https://jobs.lever.co/...)."
        )


def get_connector_for_url(url: str) -> JobSourceConnector:
    """
    Get the appropriate connector for a given job board URL.
    
    Args:
        url: Company jobs page URL
        
    Returns:
        Appropriate JobSourceConnector instance
        
    Raises:
        UnsupportedJobSourceError: If URL pattern not recognized
    """
    parsed = urlparse(url.lower())
    host = parsed.netloc
    
    # Check for Greenhouse
    if "greenhouse.io" in host:
        return GreenhouseConnector(url)
    
    # Check for Lever
    if "lever.co" in host:
        return LeverConnector(url)
    
    # Unknown source
    raise UnsupportedJobSourceError(url)


def is_supported_url(url: str) -> bool:
    """Check if a URL is from a supported job source."""
    try:
        get_connector_for_url(url)
        return True
    except UnsupportedJobSourceError:
        return False
