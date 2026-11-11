"""
Module: src.company_intelligence.job_extractor
Description: Safe HTTP fetching and HTML text extraction for target job postings,
company career pages, and public job descriptions. Enforces SSRF validation on all hops,
streaming response limits, polite headers, and graceful auth-wall / LinkedIn fallback handling.
"""

import html
import re
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests

from src.company_intelligence.validators import (
    SSRFSecurityError,
    validate_url_security,
)

# Configuration
MAX_RESPONSE_BYTES: int = int(2.5 * 1024 * 1024)  # 2.5 MB maximum
CONNECT_TIMEOUT: float = 4.0
READ_TIMEOUT: float = 6.0
MAX_REDIRECT_HOPS: int = 3

DEFAULT_HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 (NIRNAYA Career Intelligence Bot; +https://nirnaya.ai)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "DNT": "1",
}


def classify_input_source(input_str: str) -> str:
    """
    Classifies user input into:
    - 'linkedin_url'
    - 'direct_job_url'
    - 'company_url'
    - 'manual_text'
    """
    if not input_str or not isinstance(input_str, str):
        return "manual_text"

    stripped = input_str.strip()
    if not (stripped.startswith("http://") or stripped.startswith("https://")):
        return "manual_text"

    try:
        parsed = urlparse(stripped)
        domain = (parsed.netloc or "").lower()

        if "linkedin.com" in domain:
            return "linkedin_url"

        # Check common job board patterns
        job_board_indicators = [
            "greenhouse.io", "lever.co", "workday.com", "myworkdayjobs.com",
            "smartrecruiters.com", "ashbyhq.com", "bamboohr.com", "naukri.com",
            "indeed.com", "internshala.com", "wellfound.com", "angel.co",
            "/jobs", "/careers", "/job", "/position", "/vacancy"
        ]
        path_and_domain = f"{domain}{parsed.path}".lower()
        if any(ind in path_and_domain for ind in job_board_indicators):
            return "direct_job_url"

        return "company_url"
    except Exception:
        return "manual_text"


def clean_html_to_text(raw_html: str) -> str:
    """
    Extracts readable text from raw HTML, stripping scripts, styles,
    and navigation boilerplate while preserving meaningful line breaks.
    """
    if not raw_html or not isinstance(raw_html, str):
        return ""

    text = raw_html

    # Remove script, style, svg, noscript blocks
    text = re.sub(r"<(script|style|svg|noscript|header|footer|nav)[^>]*>.*?</\1>", " ", text, flags=re.DOTALL | re.IGNORECASE)

    # Convert common block tags to newlines
    text = re.sub(r"<(?:p|div|section|article|li|tr|h[1-6])[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Unescape HTML entities (&amp;, &nbsp;, etc.)
    text = html.unescape(text)

    # Normalize whitespace while preserving paragraphs
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    meaningful_lines = [line for line in lines if line]

    return "\n".join(meaningful_lines)


def fetch_job_content(url: str, resolve_dns: bool = True) -> Dict[str, Any]:
    """
    Safely fetches the HTML content of a target job or company URL.
    Validates SSRF on initial URL and each intermediate redirect.
    Enforces payload size caps and polite timeouts.

    Returns:
        Dict with keys:
            - success: bool
            - source_type: str
            - raw_text: str
            - title: Optional[str]
            - error_message: Optional[str]
            - is_login_walled: bool
            - final_url: str
    """
    source_type = classify_input_source(url)
    current_url = url.strip()

    # Step 1: Pre-fetch security validation
    is_safe, msg, ip = validate_url_security(current_url, resolve_dns=resolve_dns)
    if not is_safe:
        return {
            "success": False,
            "source_type": source_type,
            "raw_text": "",
            "title": None,
            "error_message": f"Security Validation Blocked: {msg}",
            "is_login_walled": False,
            "final_url": current_url,
        }

    # Step 2: Safe fetching loop supporting strictly validated redirects
    hops = 0
    try:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)

        while hops <= MAX_REDIRECT_HOPS:
            hops += 1

            # Validate each hop before connecting
            hop_safe, hop_msg, _ = validate_url_security(current_url, resolve_dns=resolve_dns)
            if not hop_safe:
                return {
                    "success": False,
                    "source_type": source_type,
                    "raw_text": "",
                    "title": None,
                    "error_message": f"Redirect Security Blocked: {hop_msg}",
                    "is_login_walled": False,
                    "final_url": current_url,
                }

            with session.get(
                current_url,
                headers=DEFAULT_HEADERS,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                stream=True,
                allow_redirects=False,
            ) as response:

                # Check for redirects
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("Location")
                    if not location:
                        break
                    # Resolve relative redirect URLs
                    current_url = urljoin(current_url, location)
                    continue

                # Check for client or server errors
                if response.status_code == 403 or response.status_code == 429:
                    # Specific friendly message for LinkedIn or protected sites
                    is_li = "linkedin.com" in current_url.lower()
                    return {
                        "success": False,
                        "source_type": source_type,
                        "raw_text": "",
                        "title": None,
                        "error_message": (
                            f"HTTP {response.status_code}: The target website has restricted automated access "
                            f"{'(LinkedIn authentication wall detected)' if is_li else ''}. "
                            f"Please copy and paste the job description text into the Manual Job Description tab."
                        ),
                        "is_login_walled": True,
                        "final_url": current_url,
                    }

                if response.status_code != 200:
                    return {
                        "success": False,
                        "source_type": source_type,
                        "raw_text": "",
                        "title": None,
                        "error_message": f"HTTP Error {response.status_code}: Could not retrieve page.",
                        "is_login_walled": False,
                        "final_url": current_url,
                    }

                # Stream response content with size check
                content_bytes = bytearray()
                for chunk in response.iter_content(chunk_size=8192):
                    content_bytes.extend(chunk)
                    if len(content_bytes) > MAX_RESPONSE_BYTES:
                        return {
                            "success": False,
                            "source_type": source_type,
                            "raw_text": "",
                            "title": None,
                            "error_message": f"Response exceeds safe payload limit of {MAX_RESPONSE_BYTES / (1024*1024):.1f} MB.",
                            "is_login_walled": False,
                            "final_url": current_url,
                        }

                # Decode HTML
                encoding = response.encoding or "utf-8"
                try:
                    html_content = content_bytes.decode(encoding, errors="replace")
                except Exception:
                    html_content = content_bytes.decode("utf-8", errors="replace")

                # Detect LinkedIn Auth Wall in HTML body
                if "linkedin.com" in current_url.lower():
                    lower_html = html_content.lower()
                    if "authwall" in lower_html or "sign in to view" in lower_html or "login-submit" in lower_html:
                        return {
                            "success": False,
                            "source_type": "linkedin_url",
                            "raw_text": "",
                            "title": None,
                            "error_message": (
                                "LinkedIn Authentication Wall Detected: This job requires an active LinkedIn login "
                                "to view full details. In accordance with ethical scraping and privacy guidelines, "
                                "please copy and paste the job text into the Manual Job Description tab."
                            ),
                            "is_login_walled": True,
                            "final_url": current_url,
                        }

                # Extract title
                title_match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
                extracted_title = html.unescape(title_match.group(1).strip()) if title_match else None

                # Clean to readable text
                cleaned_text = clean_html_to_text(html_content)

                if len(cleaned_text.strip()) < 50:
                    return {
                        "success": False,
                        "source_type": source_type,
                        "raw_text": cleaned_text,
                        "title": extracted_title,
                        "error_message": (
                            "Extracted page content is very short or empty (possibly dynamic client-side rendering). "
                            "Please use the Manual Job Description tab for complete accuracy."
                        ),
                        "is_login_walled": False,
                        "final_url": current_url,
                    }

                return {
                    "success": True,
                    "source_type": source_type,
                    "raw_text": cleaned_text,
                    "title": extracted_title,
                    "error_message": None,
                    "is_login_walled": False,
                    "final_url": current_url,
                }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "source_type": source_type,
            "raw_text": "",
            "title": None,
            "error_message": "Connection timed out while fetching target URL (10s limit).",
            "is_login_walled": False,
            "final_url": current_url,
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "source_type": source_type,
            "raw_text": "",
            "title": None,
            "error_message": f"Network request failed: {str(e)}",
            "is_login_walled": False,
            "final_url": current_url,
        }
    except Exception as e:
        return {
            "success": False,
            "source_type": source_type,
            "raw_text": "",
            "title": None,
            "error_message": f"Extraction error: {type(e).__name__} - {str(e)}",
            "is_login_walled": False,
            "final_url": current_url,
        }
