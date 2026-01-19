"""Resume parsing service - extracts structured profiles from resumes."""

import io
import base64
import logging

import pdfplumber
from docx import Document

from app.core.gemini_client import get_gemini_client
from app.models.schemas import ResumeProfile

logger = logging.getLogger(__name__)

RESUME_EXTRACTION_PROMPT = """You are a resume parser. Extract key information from the resume into structured format.

For skills: Include technical skills, programming languages, frameworks, tools, and soft skills.
For experience: Include brief descriptions of work experience, internships, and projects.
For education: Include degrees, institutions, and relevant coursework.
For keywords: Include industry terms, technologies, certifications, and role-related terms.

Be comprehensive but concise. Use lowercase for skills and keywords."""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file."""
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())


async def parse_resume(
    resume_text: str | None = None,
    resume_file_base64: str | None = None,
) -> ResumeProfile:
    """
    Parse a resume and extract structured profile.
    
    Args:
        resume_text: Plain text resume content
        resume_file_base64: Base64-encoded PDF or DOCX file
        
    Returns:
        ResumeProfile with extracted information
        
    Raises:
        ValueError: If neither text nor file provided, or file format unsupported
    """
    # Get text content
    if resume_text:
        text = resume_text
    elif resume_file_base64:
        file_bytes = base64.b64decode(resume_file_base64)
        
        # Detect file type by magic bytes
        if file_bytes[:4] == b'%PDF':
            text = extract_text_from_pdf(file_bytes)
        elif file_bytes[:2] == b'PK':  # DOCX is a ZIP file
            text = extract_text_from_docx(file_bytes)
        else:
            raise ValueError("Unsupported file format. Please use PDF or DOCX.")
    else:
        raise ValueError("Either resume_text or resume_file_base64 must be provided")
    
    if not text.strip():
        raise ValueError("Could not extract text from resume")
    
    # Use Gemini to extract structured profile
    client = get_gemini_client()
    profile = await client.extract_structured(
        prompt=RESUME_EXTRACTION_PROMPT,
        response_schema=ResumeProfile,
        content=text,
    )
    
    logger.info(f"Extracted profile with {len(profile.skills)} skills, {len(profile.experience)} experiences")
    return profile
