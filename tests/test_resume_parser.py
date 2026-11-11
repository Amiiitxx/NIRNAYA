"""
Unit tests for Module 3: Resume Skill Extraction & Parsing Engine (src/resume_parser.py)
Tests cover PDF extraction, multi-page handling, section segmentation,
curated skill matching, alias normalization, false-positive avoidance,
corrupted / empty file handling, and scanned PDF detection.
"""

import os
import io
import pytest
try:
    import pymupdf as fitz
except ImportError:
    import fitz

from src.resume_parser import (
    ResumeParser,
    parse_resume,
    extract_text_from_pdf,
    extract_sections_from_text,
    extract_skills_from_text,
    CANONICAL_SKILL_PATTERNS,
)


@pytest.fixture
def synthetic_single_page_pdf(tmp_path) -> str:
    """Creates a temporary single-page synthetic PDF with valid text."""
    pdf_path = tmp_path / "valid_resume.pdf"
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "John Doe\n"
        "Bengaluru, Karnataka\n\n"
        "TECHNICAL SKILLS\n"
        "Python, SQL, Machine Learning, AWS, Docker, Kubernetes, Scikit-learn\n\n"
        "WORK EXPERIENCE\n"
        "Senior Data Scientist | ABC Tech (2021 - Present)\n"
        "- Built NLP and Computer Vision pipelines in PyTorch.\n\n"
        "EDUCATION\n"
        "B.Tech in Computer Science - IIT Madras\n"
    )
    page.insert_text((50, 72), text)
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)


@pytest.fixture
def synthetic_multi_page_pdf(tmp_path) -> str:
    """Creates a temporary multi-page synthetic PDF."""
    pdf_path = tmp_path / "multipage_resume.pdf"
    doc = fitz.open()
    # Page 1
    page1 = doc.new_page()
    page1.insert_text((50, 72), "Jane Smith\nPage 1\nTECHNICAL SKILLS\nJava, Spring Boot, MySQL, Git, Linux")
    # Page 2
    page2 = doc.new_page()
    page2.insert_text((50, 72), "WORK EXPERIENCE\nPage 2\nFull-Stack Engineer at XYZ Corp\nDeployed React and Docker applications on GCP.")
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)


@pytest.fixture
def synthetic_scanned_pdf(tmp_path) -> str:
    """Creates a temporary blank/scanned PDF with no selectable text layer."""
    pdf_path = tmp_path / "scanned_resume.pdf"
    doc = fitz.open()
    doc.new_page()  # Blank page with 0 text
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)


# ---------------------------------------------------------
# PDF INGESTION & TEXT EXTRACTION TESTS
# ---------------------------------------------------------

def test_valid_single_page_pdf_extraction(synthetic_single_page_pdf):
    """Verify text extraction from a valid single-page PDF."""
    result = parse_resume(synthetic_single_page_pdf)
    assert result["extraction_status"] == "SUCCESS"
    assert "John Doe" in result["extracted_text"]
    assert result["skill_count"] >= 6
    assert "Python" in result["extracted_skills"]
    assert "AWS" in result["extracted_skills"]
    assert "Docker" in result["extracted_skills"]
    assert len(result["warnings"]) == 0


def test_multi_page_pdf_extraction(synthetic_multi_page_pdf):
    """Verify text extraction across all pages of a multi-page PDF."""
    result = parse_resume(synthetic_multi_page_pdf)
    assert result["extraction_status"] == "SUCCESS"
    assert "Jane Smith" in result["extracted_text"]
    assert "Full-Stack Engineer" in result["extracted_text"]
    # Skills across both pages
    assert "Java" in result["extracted_skills"]
    assert "React" in result["extracted_skills"]
    assert "GCP" in result["extracted_skills"]
    assert "Docker" in result["extracted_skills"]


def test_scanned_or_no_text_pdf_handling(synthetic_scanned_pdf):
    """Verify that a PDF with no selectable text produces a clear warning that OCR is not supported."""
    result = parse_resume(synthetic_scanned_pdf)
    assert result["extraction_status"] == "WARNING"
    assert result["skill_count"] == 0
    assert len(result["warnings"]) > 0
    assert "OCR is not supported" in result["warnings"][0]


def test_empty_file_handling(tmp_path):
    """Verify empty 0-byte file handling."""
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")
    result = parse_resume(str(empty_file))
    assert result["extraction_status"] == "FAILED"
    assert "empty" in result["warnings"][0].lower()


def test_invalid_file_extension(tmp_path):
    """Verify non-PDF file rejection."""
    doc_file = tmp_path / "resume.docx"
    doc_file.write_text("This is a Word document.")
    result = parse_resume(str(doc_file))
    assert result["extraction_status"] == "FAILED"
    assert "Only PDF" in result["warnings"][0]


def test_corrupted_pdf_handling(tmp_path):
    """Verify corrupted PDF handling without crashing."""
    corrupted_file = tmp_path / "corrupted.pdf"
    corrupted_file.write_bytes(b"%PDF-1.4\ncorrupted random bytes %%EOF")
    result = parse_resume(str(corrupted_file))
    assert result["extraction_status"] == "FAILED"
    assert "Unable to open PDF" in result["warnings"][0]


def test_missing_file_handling():
    """Verify non-existent file handling returns FAILED status gracefully."""
    result = parse_resume("non_existent_resume_file_xyz123.pdf")
    assert result["extraction_status"] == "FAILED"
    assert "File not found" in result["warnings"][0]


def test_in_memory_bytes_and_bytesio():
    """Verify parser operates seamlessly on raw bytes and BytesIO without writing to disk."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "In-memory test resume with Python, SQL, and FastAPI.")
    pdf_bytes = doc.tobytes()
    doc.close()

    # Test raw bytes
    res_bytes = parse_resume(pdf_bytes, filename="stream_test.pdf")
    assert res_bytes["extraction_status"] == "SUCCESS"
    assert "Python" in res_bytes["extracted_skills"]
    assert "FastAPI" in res_bytes["extracted_skills"]

    # Test BytesIO
    res_stream = parse_resume(io.BytesIO(pdf_bytes), filename="stream_io.pdf")
    assert res_stream["extraction_status"] == "SUCCESS"
    assert "SQL" in res_stream["extracted_skills"]


# ---------------------------------------------------------
# SECTION SEGMENTATION TESTS
# ---------------------------------------------------------

def test_section_segmentation_standard():
    """Verify proper segmentation of technical skills, experience, projects, education, and certs."""
    text = (
        "Candidate Name\n"
        "City, India\n\n"
        "TECHNICAL SKILLS\n"
        "Python, Docker, SQL\n\n"
        "PROFESSIONAL EXPERIENCE\n"
        "Data Engineer at ABC\n\n"
        "PROJECTS\n"
        "ETL Pipeline project\n\n"
        "EDUCATION\n"
        "B.Tech in Computer Science\n\n"
        "CERTIFICATIONS\n"
        "AWS Certified Developer\n"
    )
    sections = extract_sections_from_text(text)
    assert "Python, Docker, SQL" in sections["skills"]
    assert "Data Engineer at ABC" in sections["experience"]
    assert "ETL Pipeline project" in sections["projects"]
    assert "B.Tech in Computer Science" in sections["education"]
    assert "AWS Certified Developer" in sections["certifications"]


def test_missing_sections_return_empty_strings():
    """Verify that when sections are absent, empty strings are returned without inventing information."""
    text = (
        "Candidate Name\n\n"
        "SKILLS\n"
        "Python, SQL\n\n"
        "EDUCATION\n"
        "B.Sc Computer Science\n"
    )
    sections = extract_sections_from_text(text)
    assert sections["skills"] != ""
    assert sections["education"] != ""
    assert sections["experience"] == ""
    assert sections["projects"] == ""
    assert sections["certifications"] == ""


# ---------------------------------------------------------
# SKILL EXTRACTION & ALIAS NORMALIZATION TESTS
# ---------------------------------------------------------

def test_alias_normalization():
    """Verify that colloquial technical aliases map accurately to canonical skill names."""
    text = "Proficient in py, k8s, postgres, sklearn, powerbi, and dl."
    skills = extract_skills_from_text(text)

    assert "Python" in skills  # py -> Python
    assert "Kubernetes" in skills  # k8s -> Kubernetes
    assert "PostgreSQL" in skills  # postgres -> PostgreSQL
    assert "Scikit-learn" in skills  # sklearn -> Scikit-learn
    assert "Power BI" in skills  # powerbi -> Power BI
    assert "Deep Learning" in skills  # dl -> Deep Learning


def test_case_insensitive_matching():
    """Verify skill extraction works across UPPERCASE, lowercase, and TitleCase."""
    text = "EXCEL, python, Machine Learning, DOCKER, kubernetes, AWS, fastAPI"
    skills = extract_skills_from_text(text)

    assert "Excel" in skills
    assert "Python" in skills
    assert "Machine Learning" in skills
    assert "Docker" in skills
    assert "Kubernetes" in skills
    assert "AWS" in skills
    assert "FastAPI" in skills


def test_duplicate_skill_removal():
    """Verify that skills mentioned repeatedly are deduplicated into a unique list."""
    text = (
        "I love Python. Python is my favorite language. I have 5 years of Python experience, "
        "and I teach Python to junior developers."
    )
    skills = extract_skills_from_text(text)
    assert skills.count("Python") == 1


def test_false_positive_avoidance():
    """Verify that partial substrings inside ordinary words do not trigger false positive skill matches."""
    # 'reacting' should not match 'React'
    # 'spying' should not match 'Python' (py)
    # 'table' should not match 'Tableau'
    # 'window' or 'good' should not match 'Go'
    # 'javascript' should not falsely trigger 'Java'
    text = (
        "I was reacting to a table in the office. He is spying on a happy cat while going to work. "
        "I wrote a script in JavaScript."
    )
    skills = extract_skills_from_text(text)

    assert "React" not in skills
    assert "Python" not in skills
    assert "Tableau" not in skills
    assert "Java" not in skills  # JavaScript is present, but standalone Java is not
    assert "JavaScript" in skills


def test_resume_parser_class_instance():
    """Verify ResumeParser object initialization and helper methods."""
    parser = ResumeParser(max_file_size_mb=5.0)
    canonical_skills = parser.get_canonical_skills()

    assert len(canonical_skills) >= 30
    assert "Python" in canonical_skills
    assert "SQL" in canonical_skills
    assert "Docker" in canonical_skills

