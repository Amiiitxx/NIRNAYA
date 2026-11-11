"""
Test Suite: tests/test_company_intelligence.py
Description: Comprehensive unit and integration tests for the Company Intelligence module.
Covers SSRF security validation, input classification, requirement extraction,
candidate comparison matrix, match scoring, targeted recommendations,
resume enhancements, and 30-60-90 day roadmaps.
"""

import pytest
from src.company_intelligence.validators import (
    validate_url_security,
    is_safe_url,
    SSRFSecurityError,
)
from src.company_intelligence.job_extractor import (
    classify_input_source,
    clean_html_to_text,
    fetch_job_content,
)
from src.company_intelligence.requirement_parser import (
    extract_job_requirements,
    classify_skills_by_importance,
    extract_skills_from_segment,
)
from src.company_intelligence.candidate_comparator import (
    compare_candidate_to_job,
    calculate_company_match_score,
    find_partial_match,
)
from src.company_intelligence.recommendation_engine import (
    generate_company_skill_recommendations,
    get_guidance_for_skill,
)
from src.company_intelligence.resume_improver import (
    generate_resume_improvements,
)
from src.company_intelligence.roadmap_generator import (
    generate_actionable_roadmap,
)
from src.company_intelligence.company_analyzer import (
    analyze_company_target,
)


# =============================================================================
# 1. SSRF SECURITY & URL VALIDATION TESTS
# =============================================================================

def test_url_security_valid_schemes():
    """Verifies that standard HTTP and HTTPS URLs pass syntax checks."""
    assert is_safe_url("https://example.com/careers/job123", resolve_dns=False)
    assert is_safe_url("http://example.org:8080/jobs", resolve_dns=False)
    assert is_safe_url("https://boards.greenhouse.io/company/jobs/456", resolve_dns=False)


def test_url_security_invalid_schemes():
    """Verifies non-HTTP protocols are rejected."""
    invalid_schemes = [
        "ftp://example.com/file.txt",
        "file:///etc/passwd",
        "gopher://example.com",
        "data:text/html;base64,PHNjcmlwdD4=",
        "javascript:alert(1)",
    ]
    for url in invalid_schemes:
        ok, msg, _ = validate_url_security(url, resolve_dns=False)
        assert not ok
        assert "Only HTTP and HTTPS" in msg


def test_url_security_blocks_localhost_and_loopback():
    """Verifies localhost and 127.0.0.0/8 loopback addresses are blocked."""
    loopback_targets = [
        "http://localhost:8501",
        "http://localhost:8000/api",
        "http://127.0.0.1:8080",
        "http://127.0.0.5:9222",
        "http://127.255.255.255",
        "http://[::1]:80",
    ]
    for url in loopback_targets:
        ok, msg, _ = validate_url_security(url, resolve_dns=False)
        assert not ok
        assert "localhost" in msg.lower() or "loopback" in msg.lower() or "ssrf" in msg.lower()


def test_url_security_blocks_private_rfc1918():
    """Verifies RFC 1918 private IPv4 networks are blocked."""
    private_ips = [
        "http://10.0.0.1/admin",
        "http://10.254.1.5:8080",
        "http://172.16.0.1/status",
        "http://172.31.255.254",
        "http://192.168.1.1/router",
        "http://192.168.0.100:80",
    ]
    for url in private_ips:
        ok, msg, _ = validate_url_security(url, resolve_dns=False)
        assert not ok
        assert "private" in msg.lower() or "ssrf" in msg.lower()


def test_url_security_blocks_cloud_metadata():
    """Verifies AWS, GCP, Azure, and Alibaba cloud metadata IP endpoints are blocked."""
    metadata_endpoints = [
        "http://169.254.169.254/latest/meta-data/",
        "http://169.254.169.254/computeMetadata/v1/",
        "http://100.100.100.200/latest/meta-data/",
        "http://169.254.170.2/v2/metadata",
    ]
    for url in metadata_endpoints:
        ok, msg, _ = validate_url_security(url, resolve_dns=False)
        assert not ok
        assert "metadata" in msg.lower() or "link-local" in msg.lower() or "ssrf" in msg.lower()


def test_url_security_blocks_unsafe_ports():
    """Verifies unsafe non-web ports are rejected."""
    unsafe_ports = [
        "https://example.com:22",
        "http://example.com:25",
        "http://example.com:3306",
        "http://example.com:5432",
        "http://example.com:6379",
        "http://example.com:27017",
    ]
    for url in unsafe_ports:
        ok, msg, _ = validate_url_security(url, resolve_dns=False)
        assert not ok
        assert "not allowed" in msg.lower()


# =============================================================================
# 2. JOB EXTRACTOR & INPUT CLASSIFICATION TESTS
# =============================================================================

def test_classify_input_source():
    """Verifies source classification across all four input modes."""
    assert classify_input_source("https://www.linkedin.com/jobs/view/123456") == "linkedin_url"
    assert classify_input_source("https://jobs.lever.co/stripe/abc-def") == "direct_job_url"
    assert classify_input_source("https://boards.greenhouse.io/figma/jobs/789") == "direct_job_url"
    assert classify_input_source("https://acme-corp.com/careers") == "direct_job_url"
    assert classify_input_source("https://acmewebsite.com") == "company_url"
    assert classify_input_source("We are looking for a Senior Python Developer with FastAPI...") == "manual_text"
    assert classify_input_source("") == "manual_text"


def test_clean_html_to_text():
    """Verifies HTML stripping and text formatting."""
    raw_html = """
    <html>
        <head><script>alert('malicious')</script><style>.test { color: red; }</style></head>
        <body>
            <header><nav>Home | Careers</nav></header>
            <h1>Senior Python Engineer</h1>
            <p>We are seeking a <strong>Data Scientist</strong> with experience in <em>FastAPI</em> &amp; SQL.</p>
            <ul>
                <li>3+ years Python</li>
                <li>Docker containerization</li>
            </ul>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    cleaned = clean_html_to_text(raw_html)
    assert "alert('malicious')" not in cleaned
    assert "color: red" not in cleaned
    assert "Copyright" not in cleaned
    assert "Senior Python Engineer" in cleaned
    assert "FastAPI & SQL" in cleaned
    assert "3+ years Python" in cleaned
    assert "Docker containerization" in cleaned


def test_fetch_job_content_blocked_url():
    """Verifies fetch_job_content immediately returns an error on blocked SSRF targets."""
    res = fetch_job_content("http://127.0.0.1:8000/internal", resolve_dns=False)
    assert not res["success"]
    assert "Security Validation Blocked" in res["error_message"]


# =============================================================================
# 3. REQUIREMENT PARSER TESTS
# =============================================================================

SYNTHETIC_JOB_DESCRIPTION = """
Company: InnovateTech AI Solutions
Role: Senior Machine Learning Engineer
Location: Bengaluru, Karnataka (Hybrid)
Experience: 3-5 years of relevant industry experience
Education: B.Tech / B.E. / M.Tech in Computer Science, Data Science, or related field

About the Role:
We are looking for a Senior Machine Learning Engineer to scale our predictive intelligence models.

Requirements (Must Have):
- 3+ years of production experience in Python and SQL.
- Strong hands-on background in Machine Learning and Scikit-learn.
- Experience building scalable REST APIs using FastAPI or Flask.
- Production deployment using Docker and Git.

Preferred Qualifications (Nice to Have):
- Experience with AWS (EC2, S3, ECS) and Kubernetes.
- Familiarity with PyTorch or TensorFlow for Deep Learning.
- Knowledge of PostgreSQL and Redis caching.
- Agile/Scrum team experience.
"""

def test_extract_job_requirements_synthetic():
    """Tests structured parsing of synthetic job description."""
    reqs = extract_job_requirements(SYNTHETIC_JOB_DESCRIPTION)

    assert reqs["company_name"] == "InnovateTech AI Solutions"
    assert reqs["job_title"] == "Senior Machine Learning Engineer"
    assert "Bengaluru" in reqs["location"]
    assert "3-5 years" in reqs["experience_required"].lower()
    assert "B.Tech" in reqs["education_required"]

    # Verify skill partitioning
    assert "Python" in reqs["mandatory_skills"]
    assert "SQL" in reqs["mandatory_skills"]
    assert "Machine Learning" in reqs["mandatory_skills"]
    assert "FastAPI" in reqs["mandatory_skills"]
    assert "Docker" in reqs["mandatory_skills"]

    assert "AWS" in reqs["preferred_skills"]
    assert "Kubernetes" in reqs["preferred_skills"]
    assert "PyTorch" in reqs["preferred_skills"]

    # Verify domain categorization
    domains = reqs["categorized_skills"]
    assert "Programming Languages" in domains
    assert "Python" in domains["Programming Languages"]
    assert "Databases" in domains
    assert "SQL" in domains["Databases"]


def test_extract_job_requirements_fallback_on_blank():
    """Verifies graceful behavior on empty or whitespace inputs."""
    reqs = extract_job_requirements("   ")
    assert reqs["company_name"] == "Not specified"
    assert reqs["job_title"] == "Not specified"
    assert reqs["mandatory_skills"] == []
    assert reqs["preferred_skills"] == []


# =============================================================================
# 4. CANDIDATE COMPARATOR & MATCH SCORING TESTS
# =============================================================================

def test_compare_candidate_to_job_full_match():
    """Verifies 100% match score when candidate possesses all mandatory and preferred skills."""
    job_reqs = {
        "mandatory_skills": ["Python", "SQL", "Docker"],
        "preferred_skills": ["AWS", "FastAPI"],
        "all_skills": ["Python", "SQL", "Docker", "AWS", "FastAPI"],
    }
    candidate_skills = ["Python", "SQL", "Docker", "AWS", "FastAPI", "Pandas"]

    res = compare_candidate_to_job(candidate_skills, job_reqs)
    assert res["match_score"] == 100.0
    assert len(res["missing_mandatory_skills"]) == 0
    assert len(res["missing_preferred_skills"]) == 0
    assert "disclaimer" in res


def test_compare_candidate_to_job_zero_match():
    """Verifies 0.0% match score when candidate has no overlapping skills."""
    job_reqs = {
        "mandatory_skills": ["Python", "Docker"],
        "preferred_skills": ["AWS"],
        "all_skills": ["Python", "Docker", "AWS"],
    }
    candidate_skills = ["Ruby", "PHP", "Angular"]

    res = compare_candidate_to_job(candidate_skills, job_reqs)
    assert res["match_score"] == 0.0
    assert "Python" in res["missing_mandatory_skills"]
    assert "Docker" in res["missing_mandatory_skills"]
    assert "AWS" in res["missing_preferred_skills"]


def test_compare_candidate_partial_matching():
    """Verifies partial credit for related framework cluster (e.g. Flask when FastAPI is requested)."""
    assert find_partial_match("FastAPI", {"Flask", "Python"}) is True
    assert find_partial_match("PostgreSQL", {"MySQL", "Python"}) is True
    assert find_partial_match("PyTorch", {"TensorFlow"}) is True
    assert find_partial_match("Python", {"Docker"}) is False

    job_reqs = {
        "mandatory_skills": ["FastAPI", "Python"],
        "preferred_skills": [],
        "all_skills": ["FastAPI", "Python"],
    }
    # Candidate has Python and Flask (partial for FastAPI)
    candidate_skills = ["Python", "Flask"]
    res = compare_candidate_to_job(candidate_skills, job_reqs)
    # Python = 1.0, FastAPI = 0.5 -> 1.5 / 2.0 = 75.0%
    assert res["match_score"] == 75.0
    assert "FastAPI" in res["partially_matched_skills"]


def test_calculate_company_match_score_formula():
    """Tests the 70/30 weighting formula boundaries."""
    # Only mandatory skills: 2 out of 4 matched
    score_mand_only = calculate_company_match_score(
        mandatory_total=4, mandatory_matched=2, mandatory_partial=0,
        preferred_total=0, preferred_matched=0, preferred_partial=0,
    )
    assert score_mand_only == 50.0

    # 4/4 mandatory (70pts) + 0/2 preferred (0pts) = 70.0
    score_mand_full_pref_zero = calculate_company_match_score(
        mandatory_total=4, mandatory_matched=4, mandatory_partial=0,
        preferred_total=2, preferred_matched=0, preferred_partial=0,
    )
    assert score_mand_full_pref_zero == 70.0


# =============================================================================
# 5. RECOMMENDATION ENGINE TESTS
# =============================================================================

def test_generate_company_skill_recommendations_priority_sorting():
    """Verifies recommendations are sorted into High, Medium, and Low priorities."""
    comparison = {
        "comparison_matrix": [
            {"skill": "Docker", "requirement_type": "Mandatory", "status": "Missing"},
            {"skill": "AWS", "requirement_type": "Preferred", "status": "Missing"},
            {"skill": "FastAPI", "requirement_type": "Mandatory", "status": "Partially Matched"},
            {"skill": "Python", "requirement_type": "Mandatory", "status": "Matched"},
            {"skill": "GraphQL", "requirement_type": "Optional", "status": "Missing"},
        ]
    }
    recs = generate_company_skill_recommendations(comparison)

    assert any(r["skill"] == "Docker" for r in recs["high_priority"])
    assert any(r["skill"] == "AWS" for r in recs["medium_priority"])
    assert any(r["skill"] == "FastAPI" for r in (recs["high_priority"] + recs["medium_priority"]))
    assert any(r["skill"] == "GraphQL" for r in recs["low_priority"])
    # Python is matched, so it must not be in recommendations
    assert not any(r["skill"] == "Python" for r in recs["all_recommendations"])


def test_get_guidance_for_skill_schema():
    """Verifies recommendation guidance contains topics, exercises, and projects."""
    guidance = get_guidance_for_skill("Docker", "Mandatory", "Missing")
    assert "why_it_matters" in guidance
    assert len(guidance["topics"]) > 0
    assert len(guidance["resources"]) > 0
    assert "exercise" in guidance
    assert "project_idea" in guidance
    assert "estimated_duration" in guidance


# =============================================================================
# 6. RESUME IMPROVER & ROADMAP GENERATOR TESTS
# =============================================================================

def test_generate_resume_improvements_ethics_and_xyz_format():
    """Verifies that resume improver follows XYZ formatting and includes ethical disclaimer."""
    job_reqs = {
        "job_title": "AI Engineer",
        "company_name": "Apex Innovations",
        "mandatory_skills": ["Python", "FastAPI", "Docker"],
        "preferred_skills": ["AWS", "Kubernetes"],
    }
    candidate_skills = ["Python"]

    res = generate_resume_improvements(candidate_skills, job_reqs)
    assert res["target_role"] == "AI Engineer"
    assert res["target_company"] == "Apex Innovations"
    assert len(res["keyword_suggestions"]) > 0
    assert any(k["keyword"] == "FastAPI" for k in res["keyword_suggestions"])
    assert len(res["bullet_rewrites"]) > 0
    # Must use XYZ pattern with bracketed placeholder
    sample_rewrite = res["bullet_rewrites"][0]["recommended_xyz_structure"]
    assert "resulting in" in sample_rewrite
    assert "quantify" in sample_rewrite or "measured" in sample_rewrite
    assert "NIRNAYA Ethics & Accuracy Guarantee" in res["anti_hallucination_guarantee"]


def test_generate_actionable_roadmap_phases():
    """Verifies creation of 30, 60, and 90-day structured roadmap plans."""
    comparison = {
        "missing_mandatory_skills": ["FastAPI", "Docker"],
        "missing_preferred_skills": ["AWS"],
        "partially_matched_skills": [],
    }
    job_reqs = {"job_title": "Backend Engineer", "company_name": "CloudScale"}

    roadmap = generate_actionable_roadmap(comparison, job_reqs)
    assert "plan_30_days" in roadmap
    assert "plan_60_days" in roadmap
    assert "plan_90_days" in roadmap

    p30 = roadmap["plan_30_days"]
    assert p30["timeframe"] == "Days 1 to 30"
    assert len(p30["weekly_milestones"]) == 4

    p60 = roadmap["plan_60_days"]
    assert p60["timeframe"] == "Days 31 to 60"

    p90 = roadmap["plan_90_days"]
    assert p90["timeframe"] == "Days 61 to 90"


# =============================================================================
# 7. END-TO-END ORCHESTRATOR TESTS
# =============================================================================

def test_analyze_company_target_end_to_end_manual():
    """Verifies full analysis flow with manual job description input."""
    candidate_skills = ["Python", "SQL", "Pandas", "Scikit-learn"]

    result = analyze_company_target(
        input_content=SYNTHETIC_JOB_DESCRIPTION,
        candidate_skills=candidate_skills,
        source_type="manual_text",
    )

    assert result["success"] is True
    assert result["source_type"] == "manual_text"
    assert result["job_requirements"]["job_title"] == "Senior Machine Learning Engineer"
    assert result["comparison_result"]["match_score"] > 0
    assert "Python" in result["comparison_result"]["matched_skills"]
    assert len(result["recommendations"]["all_recommendations"]) > 0
    assert len(result["roadmap"]["plan_30_days"]["weekly_milestones"]) == 4


def test_resume_parser_integration_with_company_intelligence():
    """Verifies that text extracted via core resume parser integrates smoothly with company analyzer."""
    from src.resume_parser import extract_skills_from_text

    synthetic_resume_text = """
    Amiiitxx - Lead Data Scientist & Full Stack Engineer
    Skills: Python, FastAPI, Machine Learning, Scikit-learn, SQL, Docker, Pandas, Streamlit.
    Experience: 4 years designing AI-powered platforms.
    """
    extracted_cand_skills = extract_skills_from_text(synthetic_resume_text)
    assert "Python" in extracted_cand_skills
    assert "FastAPI" in extracted_cand_skills

    result = analyze_company_target(
        input_content=SYNTHETIC_JOB_DESCRIPTION,
        candidate_skills=extracted_cand_skills,
        resume_text=synthetic_resume_text,
        source_type="manual_text",
    )
    assert result["success"] is True
    # Python & FastAPI are matched
    assert "Python" in result["comparison_result"]["matched_skills"]
    assert "FastAPI" in result["comparison_result"]["matched_skills"]
    assert result["comparison_result"]["match_score"] > 50.0


def test_url_security_malformed_url():
    """Verifies rejection of unparseable or oversized URLs."""
    ok, msg, _ = validate_url_security("not_a_valid_url", resolve_dns=False)
    assert not ok

    oversized = "https://example.com/" + ("a" * 3000)
    ok_over, msg_over, _ = validate_url_security(oversized, resolve_dns=False)
    assert not ok_over
    assert "exceeds maximum allowed length" in msg_over


def test_url_security_carrier_grade_nat_blocked():
    """Verifies that Carrier-Grade NAT (100.64.0.0/10) is blocked."""
    ok, msg, _ = validate_url_security("http://100.64.0.1:80", resolve_dns=False)
    assert not ok
    assert "carrier-grade nat" in msg.lower() or "ssrf" in msg.lower()


def test_empty_candidate_skills_handling():
    """Verifies that an empty candidate skill set is handled gracefully without crashing."""
    job_reqs = {
        "mandatory_skills": ["Python", "Docker"],
        "preferred_skills": ["AWS"],
        "all_skills": ["Python", "Docker", "AWS"],
    }
    res = compare_candidate_to_job([], job_reqs)
    assert res["match_score"] == 0.0
    assert len(res["matched_skills"]) == 0
    assert len(res["missing_mandatory_skills"]) == 2


def test_empty_job_requirements_handling():
    """Verifies that comparison against a job with zero requirements produces 0.0% score safely."""
    res = compare_candidate_to_job(["Python"], {"mandatory_skills": [], "preferred_skills": []})
    assert res["match_score"] == 0.0


# =============================================================================
# 8. RESUME PDF INGESTION & UNPACKING REGRESSION TESTS
# =============================================================================

def test_company_intelligence_pdf_upload_successful_parsing():
    """
    Verifies that in-memory resume PDF upload correctly unpacks exactly 4 return values:
    (extracted_text, page_count, warnings, status) without unpacking errors.
    """
    import fitz
    from src.resume_parser import extract_text_from_pdf, extract_skills_from_text

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        "Candidate: Alex Rivera\n"
        "Summary: Senior ML Platform Engineer with deep expertise.\n"
        "Technical Skills: Python, SQL, FastAPI, Docker, Kubernetes, PyTorch, Pandas\n"
        "Experience: 5 years designing distributed ML inference services."
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    # Exact function call and return structure used in Company Intelligence
    extracted_text, page_count, warnings, status = extract_text_from_pdf(pdf_bytes)

    assert status == "SUCCESS"
    assert page_count == 1
    assert len(warnings) == 0
    assert "Alex Rivera" in extracted_text
    assert "FastAPI" in extracted_text

    extracted_skills = extract_skills_from_text(extracted_text)
    assert "Python" in extracted_skills
    assert "FastAPI" in extracted_skills
    assert "Docker" in extracted_skills
    assert "Kubernetes" in extracted_skills


def test_company_intelligence_pdf_upload_parsing_failures_corrupted():
    """
    Verifies that corrupted PDF bytes fail gracefully and return a 4-tuple
    with status='FAILED' without raising ValueError or crashing the upload workflow.
    """
    from src.resume_parser import extract_text_from_pdf

    corrupted_bytes = b"%PDF-1.4\ncorrupted random bytes that cannot be parsed %%EOF"
    extracted_text, page_count, warnings, status = extract_text_from_pdf(corrupted_bytes)

    assert status == "FAILED"
    assert page_count == 0
    assert extracted_text == ""
    assert len(warnings) > 0
    assert "unable to open pdf" in warnings[0].lower()


def test_company_intelligence_pdf_upload_parsing_failures_empty():
    """
    Verifies that empty 0-byte upload fails gracefully and returns a 4-tuple
    with status='FAILED' without ValueError.
    """
    from src.resume_parser import extract_text_from_pdf

    empty_bytes = b""
    extracted_text, page_count, warnings, status = extract_text_from_pdf(empty_bytes)

    assert status == "FAILED"
    assert page_count == 0
    assert extracted_text == ""
    assert len(warnings) > 0
    assert "empty" in warnings[0].lower()


def test_company_intelligence_pdf_upload_scanned_image_warning():
    """
    Verifies that an image-only / blank PDF without a selectable text layer returns
    status='WARNING' with OCR disclaimer without crashing.
    """
    import fitz
    from src.resume_parser import extract_text_from_pdf

    doc = fitz.open()
    doc.new_page()  # 0 text selectable
    blank_bytes = doc.tobytes()
    doc.close()

    extracted_text, page_count, warnings, status = extract_text_from_pdf(blank_bytes)

    assert status == "WARNING"
    assert page_count == 1
    assert extracted_text == ""
    assert len(warnings) > 0
    assert "ocr is not supported" in warnings[0].lower()


def test_company_intelligence_pdf_upload_bytesio_stream():
    """
    Verifies that BytesIO streams (as returned by Streamlit UploadedFile) unpack
    properly into (extracted_text, page_count, warnings, status).
    """
    import io
    import fitz
    from src.resume_parser import extract_text_from_pdf

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Streamlit UploadedFile Stream: Python, SQL, Docker")
    pdf_bytes = doc.tobytes()
    doc.close()

    stream = io.BytesIO(pdf_bytes)
    extracted_text, page_count, warnings, status = extract_text_from_pdf(stream)

    assert status == "SUCCESS"
    assert page_count == 1
    assert "Streamlit" in extracted_text


# =============================================================================
# 9. REAL-WORLD TESTING & ANTI-HALLUCINATION REGRESSION TESTS
# =============================================================================

def test_actual_cv_pdf_upload_workflow():
    """
    Verifies that the actual candidate CV (AMITH_RAJ_M_cv.pdf) unpacks cleanly
    into the 4-tuple and extracts valid canonical skills.
    """
    import os
    import io
    from src.resume_parser import extract_text_from_pdf, extract_skills_from_text

    cv_path = r"C:\Users\LENOVO\Downloads\AMITH_RAJ_M_cv.pdf"
    if os.path.exists(cv_path):
        with open(cv_path, "rb") as f:
            pdf_bytes = f.read()

        # Simulate Streamlit UploadedFile with BytesIO
        stream = io.BytesIO(pdf_bytes)
        stream_bytes = stream.getvalue()

        extracted_text, page_count, warnings, status = extract_text_from_pdf(stream_bytes)

        assert status == "SUCCESS"
        assert page_count == 1
        assert len(warnings) == 0
        assert "AMITH RAJ M" in extracted_text

        skills = extract_skills_from_text(extracted_text)
        assert "Python" in skills
        assert "SQL" in skills
        assert "Machine Learning" in skills
        assert "Django" in skills


def test_generic_company_homepage_handling_google():
    """
    Verifies that generic company career portals (like careers.google.com)
    preserve the company name but flag insufficient job requirement data
    without inventing arbitrary job titles, qualifications, or skills.
    """
    from src.company_intelligence.requirement_parser import extract_job_requirements
    from src.company_intelligence.company_analyzer import analyze_company_target

    raw_homepage_text = """
    Search for your career at Google.
    Careers
    Home | Jobs | Students | How we work | How we hire | Your career | Google apps
    Explore opportunities to build what's next.
    """
    source_url = "https://careers.google.com/?utm_source=chatgpt.com"

    # 1. Requirement Parser Level
    reqs = extract_job_requirements(raw_homepage_text, source_url=source_url)
    assert reqs["company_name"] == "Google"
    assert reqs["job_title"] == "Not specified"
    assert reqs["experience_required"] == "Not specified"
    assert reqs["all_skills"] == []
    assert reqs["has_sufficient_requirements"] is False
    assert reqs["is_company_homepage"] is True

    # 2. Orchestrator Level
    res = analyze_company_target(
        input_content=raw_homepage_text,
        candidate_skills=["Python", "SQL", "Machine Learning"],
        source_type="company_url",
        source_url=source_url,
    )
    assert res["success"] is True
    assert res["has_sufficient_requirements"] is False
    assert res["is_company_homepage"] is True
    assert res["job_requirements"]["company_name"] == "Google"
    assert res["job_requirements"]["job_title"] == "Not specified"
    assert "Insufficient job requirement data" in res["error_message"]
    assert res["comparison_result"]["job_skill_count"] == 0
    assert res["comparison_result"]["comparison_matrix"] == []


def test_prevention_of_fabricated_skill_gaps_and_roadmap():
    """
    Strict anti-hallucination verification: ensures that when job requirements
    are absent, the system NEVER invents 'Advanced System Design',
    'Production Optimization', or 'Cloud Deployment' or builds a roadmap from them.
    """
    from src.company_intelligence.company_analyzer import analyze_company_target
    from src.company_intelligence.roadmap_generator import generate_actionable_roadmap

    blank_reqs = {
        "company_name": "Google",
        "job_title": "Not specified",
        "mandatory_skills": [],
        "preferred_skills": [],
        "all_skills": [],
    }
    empty_comparison = {
        "missing_mandatory_skills": [],
        "missing_preferred_skills": [],
        "partially_matched_skills": [],
    }

    # Direct roadmap generator test
    roadmap = generate_actionable_roadmap(empty_comparison, blank_reqs)
    assert roadmap["has_roadmap"] is False
    assert roadmap["plan_30_days"] == {}
    assert roadmap["plan_60_days"] == {}
    assert roadmap["plan_90_days"] == {}

    forbidden_hallucinations = [
        "Advanced System Design",
        "Production Optimization",
        "Cloud Deployment",
    ]

    for fh in forbidden_hallucinations:
        assert fh not in str(roadmap)

    # End-to-end analyzer test
    res = analyze_company_target(
        input_content="Welcome to our company website. Learn about our culture.",
        candidate_skills=["Python"],
        source_type="manual_text",
    )
    assert res["has_sufficient_requirements"] is False
    assert res["roadmap"]["has_roadmap"] is False
    for fh in forbidden_hallucinations:
        assert fh not in str(res["roadmap"])
        assert fh not in str(res["recommendations"])


def test_missing_or_blank_job_description_handling():
    """Verifies that empty or whitespace-only inputs are rejected cleanly."""
    from src.company_intelligence.company_analyzer import analyze_company_target

    res_empty = analyze_company_target("", candidate_skills=["Python"])
    assert res_empty["success"] is False
    assert "too short or empty" in res_empty["error_message"].lower()

    res_whitespace = analyze_company_target("     \n  \t   ", candidate_skills=["Python"])
    assert res_whitespace["success"] is False
    assert "too short or empty" in res_whitespace["error_message"].lower()


def test_valid_job_posting_requirements_extraction_and_roadmap():
    """Verifies that a valid job posting triggers legitimate requirements and roadmap without hallucination."""
    from src.company_intelligence.company_analyzer import analyze_company_target

    valid_spec = """
    Company: Razorpay
    Role: Senior Backend Engineer
    Requirements:
    - 4+ years experience in Python, SQL, and FastAPI.
    - Strong experience in Docker and PostgreSQL.
    Preferred:
    - Experience with Redis and Kubernetes.
    """
    res = analyze_company_target(
        input_content=valid_spec,
        candidate_skills=["Python", "SQL"],  # Missing FastAPI, Docker, PostgreSQL, Redis, Kubernetes
        source_type="manual_text",
    )
    assert res["success"] is True
    assert res["has_sufficient_requirements"] is True
    assert res["job_requirements"]["company_name"] == "Razorpay"
    assert res["job_requirements"]["job_title"] == "Senior Backend Engineer"
    assert "FastAPI" in res["comparison_result"]["missing_mandatory_skills"]
    assert "Docker" in res["comparison_result"]["missing_mandatory_skills"]
    assert res["roadmap"]["has_roadmap"] is True
    assert len(res["roadmap"]["plan_30_days"]["focus_skills"]) > 0
    # Roadmaps must only focus on real missing skills
    for skill in res["roadmap"]["plan_30_days"]["focus_skills"]:
        assert skill in res["job_requirements"]["all_skills"]



