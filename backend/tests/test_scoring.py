"""Tests for the scoring module."""

import pytest

from app.models.schemas import ResumeProfile, JobRequirements
from app.services.scoring import (
    normalize_keyword,
    build_keyword_set,
    calculate_coverage,
    infer_role_family,
    compute_match_score,
    generate_match_reasons,
    generate_gap_reasons,
)


class TestNormalizeKeyword:
    """Tests for normalize_keyword function."""
    
    def test_lowercase(self):
        assert normalize_keyword("Python") == "python"
    
    def test_strip_whitespace(self):
        assert normalize_keyword("  python  ") == "python"
    
    def test_remove_special_chars(self):
        assert normalize_keyword("C++") == "c"
        assert normalize_keyword("Node.js") == "nodejs"


class TestBuildKeywordSet:
    """Tests for build_keyword_set function."""
    
    def test_simple_list(self):
        keywords = build_keyword_set(["Python", "JavaScript", "SQL"])
        assert "python" in keywords
        assert "javascript" in keywords
        assert "sql" in keywords
    
    def test_splits_on_delimiters(self):
        keywords = build_keyword_set(["Python, JavaScript, SQL"])
        assert "python" in keywords
        assert "javascript" in keywords
        assert "sql" in keywords
    
    def test_extracts_individual_words(self):
        keywords = build_keyword_set(["machine learning"])
        assert "machine" in keywords
        assert "learning" in keywords
        assert "machine learning" in keywords
    
    def test_filters_short_words(self):
        keywords = build_keyword_set(["a", "ab", "abc"])
        assert "a" not in keywords
        # Note: 2-char words are kept (e.g., "ab", "ai", "ml")
        assert "ab" in keywords
        assert "abc" in keywords


class TestCalculateCoverage:
    """Tests for calculate_coverage function."""
    
    def test_full_coverage(self):
        resume_keywords = {"python", "sql", "aws"}
        requirements = ["Python experience", "SQL knowledge", "AWS certification"]
        coverage = calculate_coverage(resume_keywords, requirements)
        assert coverage == 1.0
    
    def test_partial_coverage(self):
        resume_keywords = {"python", "sql"}
        requirements = ["Python", "SQL", "Java", "Go"]
        coverage = calculate_coverage(resume_keywords, requirements)
        assert coverage == 0.5
    
    def test_no_coverage(self):
        resume_keywords = {"python", "sql"}
        requirements = ["Rust experience", "Blockchain knowledge"]
        coverage = calculate_coverage(resume_keywords, requirements)
        assert coverage == 0.0
    
    def test_empty_requirements_full_coverage(self):
        resume_keywords = {"python", "sql"}
        coverage = calculate_coverage(resume_keywords, [])
        assert coverage == 1.0


class TestInferRoleFamily:
    """Tests for infer_role_family function."""
    
    def test_engineering(self):
        assert infer_role_family("software engineer") == "engineering"
        assert infer_role_family("backend developer") == "engineering"
        assert infer_role_family("SWE intern") == "engineering"
    
    def test_data(self):
        assert infer_role_family("data analyst") == "data"
        assert infer_role_family("data scientist") == "data"
        assert infer_role_family("analytics intern") == "data"
    
    def test_design(self):
        assert infer_role_family("UX designer") == "design"
        assert infer_role_family("product design") == "design"
    
    def test_product(self):
        assert infer_role_family("product manager") == "product"
    
    def test_unknown(self):
        assert infer_role_family("something random") == "other"


class TestComputeMatchScore:
    """Tests for compute_match_score function."""
    
    def test_high_score_for_good_match(self):
        resume = ResumeProfile(
            skills=["python", "sql", "aws", "machine learning"],
            experience=["data analysis", "building pipelines"],
            education=["computer science degree"],
            keywords=["analytics", "dashboards", "etl"],
        )
        job_requirements = JobRequirements(
            must_have=["Python", "SQL", "data analysis"],
            nice_to_have=["AWS", "machine learning"],
            responsibilities=["build dashboards", "analyze data"],
            role_family="data",
            keywords=["analytics", "python", "sql"],
        )
        
        score = compute_match_score(resume, job_requirements, "data analyst")
        assert score.final_score >= 70
        assert score.must_have_coverage > 0.8
    
    def test_low_score_for_poor_match(self):
        resume = ResumeProfile(
            skills=["python", "django"],
            experience=["web development"],
            education=["computer science"],
            keywords=["backend", "apis"],
        )
        job_requirements = JobRequirements(
            must_have=["Java", "Spring Boot", "microservices", "Kubernetes"],
            nice_to_have=["AWS", "Docker"],
            responsibilities=["build Java services"],
            role_family="engineering",
            keywords=["java", "spring", "enterprise"],
        )
        
        score = compute_match_score(resume, job_requirements, "python developer")
        assert score.final_score < 50
        assert score.must_have_coverage < 0.5
    
    def test_role_family_bonus(self):
        resume = ResumeProfile(
            skills=["python"],
            experience=[],
            education=[],
            keywords=[],
        )
        job_requirements = JobRequirements(
            must_have=[],
            nice_to_have=[],
            responsibilities=[],
            role_family="engineering",
            keywords=[],
        )
        
        # With matching role family
        score_match = compute_match_score(resume, job_requirements, "software engineer")
        
        # With non-matching role family
        score_nomatch = compute_match_score(resume, job_requirements, "data analyst")
        
        assert score_match.role_family_bonus == 10
        assert score_nomatch.role_family_bonus == 0
        assert score_match.final_score > score_nomatch.final_score


class TestGenerateMatchReasons:
    """Tests for generate_match_reasons function."""
    
    def test_generates_at_least_three_reasons(self):
        resume = ResumeProfile(
            skills=["python", "sql"],
            experience=[],
            education=[],
            keywords=[],
        )
        job_requirements = JobRequirements(
            must_have=["Python"],
            nice_to_have=[],
            responsibilities=[],
            role_family="engineering",
            keywords=[],
        )
        from app.services.scoring import ScoreBreakdown
        score = ScoreBreakdown(
            must_have_coverage=1.0,
            nice_to_have_coverage=0.0,
            preference_match=0.5,
            role_family_bonus=10,
            final_score=75,
        )
        
        reasons = generate_match_reasons(resume, job_requirements, score)
        assert len(reasons) >= 3


class TestGenerateGapReasons:
    """Tests for generate_gap_reasons function."""
    
    def test_identifies_missing_must_haves(self):
        resume = ResumeProfile(
            skills=["python"],
            experience=[],
            education=[],
            keywords=[],
        )
        job_requirements = JobRequirements(
            must_have=["Java", "Kubernetes"],
            nice_to_have=["Docker"],
            responsibilities=[],
            role_family="engineering",
            keywords=[],
        )
        
        gaps = generate_gap_reasons(resume, job_requirements)
        assert len(gaps) > 0
        # Should identify missing Java and/or Kubernetes
        gap_text = " ".join(gaps).lower()
        assert "java" in gap_text or "kubernetes" in gap_text
    
    def test_no_gaps_when_all_covered(self):
        resume = ResumeProfile(
            skills=["python", "java", "kubernetes", "docker"],
            experience=[],
            education=[],
            keywords=[],
        )
        job_requirements = JobRequirements(
            must_have=["Python", "Java"],
            nice_to_have=["Docker", "Kubernetes"],
            responsibilities=[],
            role_family="engineering",
            keywords=[],
        )
        
        gaps = generate_gap_reasons(resume, job_requirements)
        # Should have the default "no significant gaps" message
        assert "no significant gaps" in gaps[0].lower() or len([g for g in gaps if "missing" in g.lower()]) == 0
