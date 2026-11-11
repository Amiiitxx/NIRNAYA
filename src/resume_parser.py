"""
Module: Resume Parser
Description: Production-ready PDF resume text extraction using PyMuPDF (fitz),
regex-based section segmentation, and curated technical skill extraction with
robust alias normalization and false-positive prevention.
"""

import io
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import pymupdf as fitz
except ImportError:
    import fitz


# ---------------------------------------------------------
# CONSTANTS & CONFIGURATION
# ---------------------------------------------------------

DEFAULT_MAX_FILE_SIZE_MB: float = 10.0
MIN_TEXT_LENGTH_THRESHOLD: int = 40  # Under 40 chars indicates scanned / image-only PDF

# Canonical section names mapped to regex patterns matching section headings
SECTION_HEADING_PATTERNS: Dict[str, re.Pattern] = {
    "skills": re.compile(
        r"^(?:\d+[\.\)]\s*)?(?:technical\s+skills|skills\s*(?:&|and)?\s*technologies|core\s+competencies|"
        r"technical\s+competencies|skills\s*(?:&|and)?\s*tools|skills|programming\s+languages|"
        r"tools\s*(?:&|and)?\s*technologies|key\s+skills)\s*:?$",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^(?:\d+[\.\)]\s*)?(?:work\s+experience|professional\s+experience|experience|employment\s+history|"
        r"career\s+history|career\s+summary|relevant\s+experience|work\s+history)\s*:?$",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^(?:\d+[\.\)]\s*)?(?:technical\s+projects|projects|personal\s+projects|academic\s+projects|"
        r"key\s+projects|selected\s+projects)\s*:?$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:\d+[\.\)]\s*)?(?:education|academic\s+background|academic\s+qualifications|"
        r"educational\s+qualifications|qualifications|academic\s+history)\s*:?$",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^(?:\d+[\.\)]\s*)?(?:certifications|certificates|licenses\s*(?:&|and)?\s*certifications|"
        r"professional\s+certifications|trainings\s*(?:&|and)?\s*certifications)\s*:?$",
        re.IGNORECASE,
    ),
}

# Curated Technical Skill Dictionary: Canonical Name -> Regex with Word Boundaries and Aliases
CANONICAL_SKILL_PATTERNS: Dict[str, str] = {
    # Programming Languages
    "Python": r"\b(?:python|py)\b",
    "Java": r"\bjava(?!\s*script)\b",
    "JavaScript": r"\b(?:javascript|js)\b",
    "TypeScript": r"\b(?:typescript|ts)\b",
    "C++": r"(?:\bc\+\+|\bcpp\b)",
    "SQL": r"\bsql\b",
    "HTML/CSS": r"\b(?:html5?|css3?)\b",

    # Data Science, Machine Learning & AI
    "Machine Learning": r"\b(?:machine\s+learning|ml)\b",
    "Deep Learning": r"\b(?:deep\s+learning|dl)\b",
    "NLP": r"\b(?:nlp|natural\s+language\s+processing)\b",
    "Computer Vision": r"\bcomputer\s+vision\b",
    "PyTorch": r"\bpytorch\b",
    "TensorFlow": r"\b(?:tensorflow|tf)\b",
    "Scikit-learn": r"\b(?:scikit[\s_-]*learn|sklearn)\b",
    "Pandas": r"\bpandas\b",
    "NumPy": r"\bnumpy\b",
    "Statistics": r"\b(?:statistics|statistical\s+modeling|statistical\s+analysis)\b",

    # Web & API Frameworks
    "FastAPI": r"\b(?:fast[\s_-]*api|fastapi)\b",
    "Flask": r"\bflask\b",
    "Django": r"\bdjango\b",
    "React": r"\b(?:react|react[\s._-]*js)\b",
    "Node.js": r"\b(?:node[\s._-]*js|nodejs)\b",

    # Cloud, DevOps & Containers
    "AWS": r"\b(?:aws|amazon\s+web\s+services)\b",
    "Azure": r"\b(?:azure|microsoft\s+azure)\b",
    "GCP": r"\b(?:gcp|google\s+cloud(?:\s+platform)?)\b",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\b(?:kubernetes|k8s)\b",
    "Git": r"\b(?:git|github|gitlab)\b",
    "Linux": r"\blinux\b",

    # Big Data & Data Engineering
    "Spark": r"\b(?:apache\s+spark|spark)\b",
    "Hadoop": r"\b(?:apache\s+hadoop|hadoop)\b",
    "Airflow": r"\b(?:apache\s+airflow|airflow)\b",
    "Kafka": r"\b(?:apache\s+kafka|kafka)\b",
    "dbt": r"\bdbt\b",
    "Snowflake": r"\bsnowflake\b",
    "BigQuery": r"\bbigquery\b",

    # Databases
    "PostgreSQL": r"\b(?:postgresql|postgres|pgsql)\b",
    "MySQL": r"\bmysql\b",
    "MongoDB": r"\b(?:mongodb|mongo)\b",
    "Redis": r"\bredis\b",

    # BI & Analytics Tools
    "Power BI": r"\b(?:power[\s._-]*bi|ms\s*power[\s._-]*bi)\b",
    "Tableau": r"\btableau\b",
    "Excel": r"\b(?:ms\s*excel|excel|microsoft\s*excel)\b",
}

# Precompile skill regex patterns for high-throughput evaluation
COMPILED_SKILL_PATTERNS: Dict[str, re.Pattern] = {
    skill: re.compile(pattern, re.IGNORECASE)
    for skill, pattern in CANONICAL_SKILL_PATTERNS.items()
}


# ---------------------------------------------------------
# TEXT EXTRACTION & SECTION SEGMENTATION FUNCTIONS
# ---------------------------------------------------------

def extract_text_from_pdf(
    source: Union[str, bytes, io.BytesIO, os.PathLike],
    max_size_mb: float = DEFAULT_MAX_FILE_SIZE_MB,
) -> Tuple[str, int, List[str], str]:
    """
    Extracts text from all readable pages of a PDF document using PyMuPDF.

    Args:
        source: File path, byte buffer, or BytesIO stream of the PDF.
        max_size_mb: Maximum allowed file size in megabytes.

    Returns:
        Tuple containing:
        - extracted_text (str): Preserved document text.
        - page_count (int): Total number of pages.
        - warnings (List[str]): List of warning/error messages.
        - status (str): 'SUCCESS', 'WARNING', or 'FAILED'.
    """
    warnings: List[str] = []

    # 1. Source type & size validation
    raw_bytes: Optional[bytes] = None

    if isinstance(source, (str, os.PathLike)):
        file_path_str = str(source)
        if not os.path.exists(file_path_str):
            return "", 0, [f"File not found: '{os.path.basename(file_path_str)}'"], "FAILED"

        # Validate file extension
        if not file_path_str.lower().endswith(".pdf"):
            ext = os.path.splitext(file_path_str)[1] or "unknown"
            return "", 0, [f"Invalid file format: '{ext}'. Only PDF (.pdf) documents are supported."], "FAILED"

        # Validate file size
        file_size_bytes = os.path.getsize(file_path_str)
        max_bytes = max_size_mb * 1024 * 1024
        if file_size_bytes > max_bytes:
            size_mb = file_size_bytes / (1024 * 1024)
            return "", 0, [f"File size ({size_mb:.2f} MB) exceeds maximum allowed limit of {max_size_mb:.1f} MB."], "FAILED"

        try:
            with open(file_path_str, "rb") as f:
                raw_bytes = f.read()
        except Exception as e:
            return "", 0, [f"Unable to read file: {type(e).__name__}"], "FAILED"

    elif isinstance(source, bytes):
        raw_bytes = source
        max_bytes = max_size_mb * 1024 * 1024
        if len(raw_bytes) > max_bytes:
            size_mb = len(raw_bytes) / (1024 * 1024)
            return "", 0, [f"File size ({size_mb:.2f} MB) exceeds maximum allowed limit of {max_size_mb:.1f} MB."], "FAILED"

    elif isinstance(source, io.BytesIO):
        raw_bytes = source.getvalue()
        max_bytes = max_size_mb * 1024 * 1024
        if len(raw_bytes) > max_bytes:
            size_mb = len(raw_bytes) / (1024 * 1024)
            return "", 0, [f"File size ({size_mb:.2f} MB) exceeds maximum allowed limit of {max_size_mb:.1f} MB."], "FAILED"

    else:
        return "", 0, [f"Unsupported source type: '{type(source).__name__}'. Expected file path, bytes, or BytesIO."], "FAILED"

    # Empty payload check
    if not raw_bytes or len(raw_bytes) == 0:
        return "", 0, ["The provided PDF file is empty (0 bytes)."], "FAILED"

    # 2. PyMuPDF In-Memory Document Ingestion
    doc = None
    try:
        doc = fitz.open(stream=raw_bytes, filetype="pdf")
    except Exception as e:
        return "", 0, ["Unable to open PDF document. File may be corrupted, invalid, or encrypted."], "FAILED"

    try:
        # Check password / encryption
        if getattr(doc, "is_encrypted", False) and getattr(doc, "needs_pass", False):
            return "", 0, ["The PDF is password-protected or encrypted. Please remove password protection before uploading."], "FAILED"

        page_count = doc.page_count
        if page_count == 0:
            return "", 0, ["The PDF document contains 0 pages."], "FAILED"

        # 3. Extract text page by page preserving line breaks
        page_texts: List[str] = []
        for page_idx in range(page_count):
            page = doc[page_idx]
            text = page.get_text("text")
            if text:
                page_texts.append(text)

        full_text = "\n\n".join(page_texts).strip()

        # 4. Check for scanned / image-only documents
        cleaned_len = len(re.sub(r"\s+", "", full_text))
        if cleaned_len < MIN_TEXT_LENGTH_THRESHOLD:
            warnings.append(
                "Document appears to be a scanned image or contains no selectable text layer. "
                "OCR is not supported; please upload a text-based PDF generated from Word, LaTeX, or Google Docs."
            )
            return full_text, page_count, warnings, "WARNING"

        return full_text, page_count, warnings, "SUCCESS"

    except Exception as e:
        return "", 0, [f"Error extracting text from PDF: {type(e).__name__}"], "FAILED"
    finally:
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass


def extract_sections_from_text(text: str) -> Dict[str, str]:
    """
    Segments resume text into standard sections (skills, experience, projects,
    education, certifications) based on line-level heading identification.

    If a section cannot be identified, its value is an empty string.

    Args:
        text: Raw extracted resume text.

    Returns:
        Dict mapping section names to extracted section text.
    """
    sections: Dict[str, List[str]] = {
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
        "certifications": [],
    }

    if not text or not text.strip():
        return {k: "" for k in sections}

    lines = [line.strip() for line in text.split("\n")]
    current_section: Optional[str] = None

    for line in lines:
        if not line:
            continue

        # Check if line matches a known section header
        matched_section: Optional[str] = None
        for sec_name, pattern in SECTION_HEADING_PATTERNS.items():
            if pattern.match(line):
                matched_section = sec_name
                break

        if matched_section:
            current_section = matched_section
        elif current_section:
            sections[current_section].append(line)

    return {sec_name: "\n".join(lines_list).strip() for sec_name, lines_list in sections.items()}


def extract_skills_from_text(text: str) -> List[str]:
    """
    Identifies technical skills from text using curated regex matching with
    word boundaries and alias normalization.

    Prevents partial-word false positives, avoids duplicates, and returns
    canonical skill names in alphabetical order.

    Args:
        text: Resume text or section text.

    Returns:
        List of unique canonical skill names detected in the text.
    """
    if not text or not text.strip():
        return []

    found_skills: set = set()

    for canonical_name, pattern in COMPILED_SKILL_PATTERNS.items():
        if pattern.search(text):
            found_skills.add(canonical_name)

    return sorted(list(found_skills))


# ---------------------------------------------------------
# UNIFIED RESUME PARSER API
# ---------------------------------------------------------

class ResumeParser:
    """
    Thread-safe, privacy-preserving resume parsing engine for extracting
    selectable text, sections, and technical skills from PDF documents.
    """

    def __init__(self, max_file_size_mb: float = DEFAULT_MAX_FILE_SIZE_MB):
        self.max_file_size_mb = max_file_size_mb
        self.skill_patterns = COMPILED_SKILL_PATTERNS

    def parse(
        self,
        file_source: Union[str, bytes, io.BytesIO, os.PathLike],
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Parses resume from file path, bytes, or BytesIO stream.
        """
        return parse_resume(
            file_source=file_source,
            filename=filename,
            max_size_mb=self.max_file_size_mb,
        )

    @staticmethod
    def extract_text(
        file_source: Union[str, bytes, io.BytesIO, os.PathLike],
        max_size_mb: float = DEFAULT_MAX_FILE_SIZE_MB,
    ) -> Tuple[str, int, List[str], str]:
        return extract_text_from_pdf(file_source, max_size_mb=max_size_mb)

    @staticmethod
    def extract_sections(text: str) -> Dict[str, str]:
        return extract_sections_from_text(text)

    @staticmethod
    def extract_skills(text: str) -> List[str]:
        return extract_skills_from_text(text)

    @staticmethod
    def get_canonical_skills() -> List[str]:
        return sorted(list(CANONICAL_SKILL_PATTERNS.keys()))


def parse_resume(
    file_source: Union[str, bytes, io.BytesIO, os.PathLike],
    filename: Optional[str] = None,
    max_size_mb: float = DEFAULT_MAX_FILE_SIZE_MB,
) -> Dict[str, Any]:
    """
    Primary reusable API function for parsing resumes.

    Args:
        file_source: Path to PDF file, raw bytes, or BytesIO stream.
        filename: Optional human-readable filename for reporting.
        max_size_mb: Maximum allowed file size in MB.

    Returns:
        Structured dictionary:
        {
            "filename": str,
            "extracted_text": str,
            "sections": Dict[str, str],
            "extracted_skills": List[str],
            "skill_count": int,
            "extraction_status": "SUCCESS" | "WARNING" | "FAILED",
            "warnings": List[str],
        }
    """
    # Determine human-readable filename safely
    if filename:
        safe_filename = os.path.basename(str(filename))
    elif isinstance(file_source, (str, os.PathLike)):
        safe_filename = os.path.basename(str(file_source))
    else:
        safe_filename = "uploaded_resume.pdf"

    default_sections = {
        "skills": "",
        "experience": "",
        "projects": "",
        "education": "",
        "certifications": "",
    }

    # 1. Extract text from PDF
    extracted_text, page_count, warnings, status = extract_text_from_pdf(
        source=file_source,
        max_size_mb=max_size_mb,
    )

    if status == "FAILED":
        return {
            "filename": safe_filename,
            "extracted_text": "",
            "sections": default_sections,
            "extracted_skills": [],
            "skill_count": 0,
            "extraction_status": "FAILED",
            "warnings": warnings,
        }

    # 2. Extract sections
    sections = extract_sections_from_text(extracted_text)

    # 3. Extract technical skills
    extracted_skills = extract_skills_from_text(extracted_text)

    return {
        "filename": safe_filename,
        "extracted_text": extracted_text,
        "sections": sections,
        "extracted_skills": extracted_skills,
        "skill_count": len(extracted_skills),
        "extraction_status": status,
        "warnings": warnings,
    }
