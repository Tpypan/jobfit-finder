"""Deterministic scoring algorithm for job-resume matching."""

import re
from dataclasses import dataclass

from app.models.schemas import ResumeProfile, JobRequirements


@dataclass
class ScoreBreakdown:
    """Breakdown of score components."""
    must_have_coverage: float  # 0-1
    nice_to_have_coverage: float  # 0-1
    preference_match: float  # 0-1
    role_family_bonus: int  # 0 or 10
    final_score: int  # 0-100


def normalize_keyword(keyword: str) -> str:
    """Normalize a keyword for matching."""
    # Lowercase, strip, remove special chars
    normalized = keyword.lower().strip()
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return normalized


def build_keyword_set(items: list[str]) -> set[str]:
    """Build a set of normalized keywords from a list of items."""
    keywords = set()
    for item in items:
        # Split on common delimiters and add each part
        parts = re.split(r'[,;/\n]', item)
        for part in parts:
            normalized = normalize_keyword(part)
            if normalized and len(normalized) > 1:
                keywords.add(normalized)
                # Also add individual words for multi-word phrases
                for word in normalized.split():
                    if len(word) > 2:
                        keywords.add(word)
    return keywords


def calculate_coverage(resume_keywords: set[str], requirement_items: list[str]) -> float:
    """
    Calculate what percentage of requirement items are covered by resume keywords.
    
    Returns float from 0 to 1.
    """
    if not requirement_items:
        return 1.0  # No requirements = full coverage
    
    matched = 0
    for item in requirement_items:
        item_keywords = build_keyword_set([item])
        # Check if any of the item's keywords match resume keywords
        if item_keywords & resume_keywords:
            matched += 1
    
    return matched / len(requirement_items)


def infer_role_family(desired_description: str) -> str:
    """Infer role family from user's desired job description."""
    desc_lower = desired_description.lower()
    
    role_keywords = {
        "engineering": ["engineer", "developer", "software", "swe", "backend", "frontend", "full-stack", "fullstack", "devops", "sre"],
        "data": ["data", "analyst", "analytics", "scientist", "ml", "machine learning", "ai", "bi"],
        "design": ["design", "ux", "ui", "product design", "graphic", "visual"],
        "product": ["product manager", "pm", "product owner", "product lead"],
        "marketing": ["marketing", "growth", "seo", "content", "social media", "brand"],
        "sales": ["sales", "account", "business development", "bdr", "sdr"],
        "operations": ["operations", "ops", "supply chain", "logistics"],
        "finance": ["finance", "accounting", "financial", "controller", "treasury"],
        "hr": ["hr", "human resources", "recruiting", "recruiter", "people"],
        "legal": ["legal", "counsel", "attorney", "lawyer", "compliance"],
    }
    
    for family, keywords in role_keywords.items():
        if any(kw in desc_lower for kw in keywords):
            return family
    
    return "other"


def compute_match_score(
    resume_profile: ResumeProfile,
    job_requirements: JobRequirements,
    desired_description: str,
) -> ScoreBreakdown:
    """
    Compute deterministic match score between resume and job.
    
    Args:
        resume_profile: Extracted resume profile
        job_requirements: Extracted job requirements
        desired_description: User's desired job description
        
    Returns:
        ScoreBreakdown with component scores and final score
    """
    # Build resume keyword set from all profile fields
    resume_keywords = build_keyword_set(
        resume_profile.skills + 
        resume_profile.experience + 
        resume_profile.education + 
        resume_profile.keywords
    )
    
    # Add desired description keywords
    desired_keywords = build_keyword_set([desired_description])
    combined_keywords = resume_keywords | desired_keywords
    
    # Calculate must-have coverage (weight: 40%)
    must_have_coverage = calculate_coverage(combined_keywords, job_requirements.must_have)
    
    # Calculate nice-to-have coverage (weight: 20%)
    nice_to_have_coverage = calculate_coverage(combined_keywords, job_requirements.nice_to_have)
    
    # Calculate preference match - how well job matches user's desired description (weight: 30%)
    job_keywords = build_keyword_set(job_requirements.keywords + job_requirements.responsibilities)
    if desired_keywords and job_keywords:
        preference_match = len(desired_keywords & job_keywords) / len(desired_keywords)
    else:
        preference_match = 0.5  # Neutral if no desired keywords
    
    # Role family bonus (weight: 10 points)
    inferred_family = infer_role_family(desired_description)
    role_family_bonus = 10 if job_requirements.role_family == inferred_family else 0
    
    # Calculate final score
    base_score = (
        must_have_coverage * 40 +
        nice_to_have_coverage * 20 +
        preference_match * 30 +
        role_family_bonus
    )
    
    # Apply penalty if must-have coverage is very low
    if must_have_coverage < 0.3:
        base_score -= 15
    
    # Clip to 0-100
    final_score = max(0, min(100, int(base_score)))
    
    return ScoreBreakdown(
        must_have_coverage=must_have_coverage,
        nice_to_have_coverage=nice_to_have_coverage,
        preference_match=preference_match,
        role_family_bonus=role_family_bonus,
        final_score=final_score,
    )


def generate_match_reasons(
    resume_profile: ResumeProfile,
    job_requirements: JobRequirements,
    score_breakdown: ScoreBreakdown,
) -> list[str]:
    """Generate human-readable reasons for the match."""
    reasons = []
    
    resume_keywords = build_keyword_set(
        resume_profile.skills + resume_profile.keywords
    )
    
    # Find matched must-haves
    matched_must_haves = []
    for item in job_requirements.must_have[:5]:
        item_keywords = build_keyword_set([item])
        if item_keywords & resume_keywords:
            matched_must_haves.append(item)
    
    if matched_must_haves:
        for item in matched_must_haves[:3]:
            reasons.append(f"Matches requirement: {item}")
    
    # Responsibility alignment
    matched_responsibilities = []
    for resp in job_requirements.responsibilities[:5]:
        resp_keywords = build_keyword_set([resp])
        if resp_keywords & resume_keywords:
            matched_responsibilities.append(resp)
    
    if matched_responsibilities:
        reasons.append(f"Experience aligns with: {matched_responsibilities[0]}")
    
    # Nice-to-haves matched
    matched_nice = []
    for item in job_requirements.nice_to_have[:3]:
        item_keywords = build_keyword_set([item])
        if item_keywords & resume_keywords:
            matched_nice.append(item)
    
    if matched_nice:
        reasons.append(f"Has preferred skill: {matched_nice[0]}")
    
    # Role family match
    if score_breakdown.role_family_bonus > 0:
        reasons.append(f"Role type matches desired: {job_requirements.role_family}")
    
    # Ensure we have at least 3 reasons
    while len(reasons) < 3:
        reasons.append("Profile shows relevant background")
    
    return reasons[:6]  # Cap at 6


def generate_gap_reasons(
    resume_profile: ResumeProfile,
    job_requirements: JobRequirements,
) -> list[str]:
    """Generate human-readable gaps between resume and job."""
    gaps = []
    
    resume_keywords = build_keyword_set(
        resume_profile.skills + 
        resume_profile.experience + 
        resume_profile.keywords
    )
    
    # Find unmatched must-haves
    for item in job_requirements.must_have:
        item_keywords = build_keyword_set([item])
        if not (item_keywords & resume_keywords):
            gaps.append(f"Missing requirement: {item}")
    
    # Find unmatched nice-to-haves  
    for item in job_requirements.nice_to_have:
        item_keywords = build_keyword_set([item])
        if not (item_keywords & resume_keywords):
            gaps.append(f"Missing preferred skill: {item}")
    
    # Limit to 5 gaps
    return gaps[:5] if gaps else ["No significant gaps identified"]
