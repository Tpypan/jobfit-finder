"""Gemini API client for structured extraction."""

import json
import logging
from typing import TypeVar, Type

import google.generativeai as genai
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    """Client for Gemini API with structured JSON extraction."""
    
    def __init__(self):
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
    
    async def extract_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        content: str,
    ) -> T:
        """
        Extract structured data from content using Gemini.
        
        Args:
            prompt: System prompt describing the extraction task
            response_schema: Pydantic model for the expected response
            content: The content to extract from
            
        Returns:
            Parsed Pydantic model instance
        """
        schema_json = response_schema.model_json_schema()
        
        full_prompt = f"""{prompt}

Extract the information from the following content and return ONLY valid JSON matching this schema:
{json.dumps(schema_json, indent=2)}

Content to analyze:
---
{content}
---

Return ONLY the JSON object, no markdown formatting or explanations."""

        try:
            response = await self.model.generate_content_async(full_prompt)
            response_text = response.text.strip()
            
            # Clean up response if wrapped in markdown
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            
            data = json.loads(response_text)
            return response_schema.model_validate(data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")
        except Exception as e:
            logger.error(f"Gemini extraction failed: {e}")
            raise


# Global client instance
_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    """Get or create the global Gemini client."""
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
