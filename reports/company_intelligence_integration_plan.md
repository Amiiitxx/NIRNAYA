# NIRNAYA – Additive Feature Integration Plan (Phase 1 Final Review)
## Module: Company-Specific Skill Gap Analysis & Career Improvement

- **Platform Name:** NIRNAYA
- **Tagline:** *"Intelligence That Drives Decisions."*
- **Platform Creator:** Amiiitxx
- **Integration Type:** 100% Additive, Independent, Non-Destructive Extension
- **Plan Status:** Phase 1 Final Safety Review Completed (Awaiting Phase 2 Approval)

---

## 1. Executive Summary & Protection Commitments

The goal of this initiative is to introduce a new independent capability into NIRNAYA: **Company-Specific Skill Gap Analysis & Career Improvement**.

This feature empowers tech professionals and job candidates to evaluate their skills against **specific company job postings or career requirements** (via Direct URL, Company Career Page URL, LinkedIn Job URL, or Manual Job Description Input), compare their resume profile, receive targeted learning roadmaps (30/60/90 days), and obtain job-specific resume enhancement suggestions without inventing false credentials.

### Strict Protection Commitments
1. **No Overwriting or Redesign:** Existing dashboard layout, colors (`#3A0353`, `#4B0968`, `#F59E51`, `#F8D299`), typography, and components remain preserved.
2. **No Regression on Models or Data:** The trained Gradient Boosting and XGBoost salary prediction models, 72-dimension feature pipelines, and cleaned datasets (`cleaned_job_market_all.csv`, `cleaned_salary_model_data.csv`) will **not** be modified, retrained, or replaced.
3. **No Database Schema Alterations:** The existing relational schema (`companies`, `skills`, `job_postings`, `job_skills`) remains untouched. Analysis is session-based and memory-resident.
4. **No API Breakages:** Existing FastAPI endpoints (`/api/market/*`) remain completely unaffected in path, method, schema, and behavior.
5. **No Technology Swaps:** The project retains Python, Streamlit, FastAPI, SQLAlchemy, Scikit-learn, and PyMuPDF. **Django will not be introduced**.
6. **Regression Test Guarantee:** All **86 existing tests** must continue to pass with a 100% success rate alongside new feature tests.

---

## 2. API Endpoint Reconciliation (9 vs 13 Endpoint Count)

### Exact Enumeration of Existing API Endpoints
An inspection of `api/main.py` reconciles the endpoint count:
- **9 Custom Application Endpoints:** Defined and implemented in `api/main.py`.
- **4 Built-in FastAPI Infrastructure Endpoints:** Automatically registered by the FastAPI framework for OpenAPI documentation and schema distribution.
- **Total Registered Routes on `app.routes`:** Exactly **13 routes**.

| # | HTTP Method | Path | Category | Response Model / Handler | Notes |
| :---: | :---: | :--- | :--- | :--- | :--- |
| **1** | `GET` | `/health` | Application | `HealthResponse` | System health, DB connection, dataset status |
| **2** | `GET` | `/api/market/overview` | Application | `MarketOverviewResponse` | High-level market KPIs & distributions |
| **3** | `GET` | `/api/market/job-roles` | Application | `JobRolesResponse` | In-demand tech roles with count & share |
| **4** | `GET` | `/api/market/cities` | Application | `CitiesResponse` | Hiring concentration & state distributions |
| **5** | `GET` | `/api/market/skills` | Application | `SkillsResponse` | In-demand skills & top co-occurrence pairs |
| **6** | `GET` | `/api/market/salary` | Application | `SalaryAnalyticsResponse` | Verified compensation benchmarks by role/city |
| **7** | `GET` | `/api/market/trends` | Application | `TrendsResponse` | Monthly and quarterly posting volumes |
| **8** | `GET` | `/api/market/role/{job_role}` | Application | `Dict[str, Any]` (`get_single_role`) | 360-degree role-specific dossier |
| **9** | `GET` | `/api/market/city/{city}` | Application | `Dict[str, Any]` (`get_single_city`) | 360-degree city-specific dossier |
| *10* | `GET` | `/openapi.json` | Framework | `JSONResponse` | OpenAPI 3.1 JSON schema specification |
| *11* | `GET` | `/docs` | Framework | `HTMLResponse` | Swagger UI documentation interface |
| *12* | `GET` | `/docs/oauth2-redirect`| Framework | `HTMLResponse` | Swagger OAuth2 redirect handler |
| *13* | `GET` | `/redoc` | Framework | `HTMLResponse` | ReDoc interactive documentation interface |

### Test Suite Alignment
In [`tests/test_api.py`](file:///c:/Users/LENOVO/OneDrive/Desktop/Applet%20logic/Data%20Science/india_job_market_internship_dataset/project_anti/tests/test_api.py), there are exactly **9 dedicated test functions**, one for each of the 9 application endpoints. All 9 pass in the baseline test suite.

### Confirmation of Zero API Impact
The proposed Company Intelligence module operates primarily in session memory within the Streamlit UI. **No existing API endpoint, URL route, request parameter, response schema, or business logic will be modified.** If a dedicated API endpoint (e.g. `POST /api/company/analyze`) is added in a later phase, it will be registered as a completely isolated new route without touching any of the 9 existing endpoints.

---

## 3. SSRF Security Architecture & Ingestion Safeguards

Web scrapers and URL fetchers that accept user-provided URLs present significant Server-Side Request Forgery (SSRF) and Denial of Service (DoS) risks if not fortified. The proposed URL ingestion module ([`src/company_intelligence/validators.py`](file:///c:/Users/LENOVO/OneDrive/Desktop/Applet%20logic/Data%20Science/india_job_market_internship_dataset/project_anti/src/company_intelligence/validators.py)) implements defense-in-depth:

```
[User Input URL]
       │
       ▼
[1. Scheme & Port Check] ──► Reject non-http/https, Reject unsafe ports
       │
       ▼
[2. Hostname DNS Resolution] ──► Query socket.getaddrinfo (IPv4 & IPv6)
       │
       ▼
[3. IP Range & IMDS Validation] ──► Block Loopback, Private, Link-Local, Metadata
       │
       ▼
[4. Safe HTTP Fetch (Pinned IP)] ──► Max 8s Timeout, Max 2.5 MB Stream
       │
       ▼
[5. Redirect Target Check] ──► Validate each 'Location' hop recursively
       │
       ▼
[Clean Response Text]
```

### 1. Protocol & Port Enforcement
- **Permitted Schemes:** Strictly `http://` and `https://`. All others (`file://`, `ftp://`, `gopher://`, `data:`, `javascript:`, `expect://`) are rejected immediately.
- **Permitted Ports:** Only standard web ports `80`, `443`, `8080`, and `8443`. Requests to internal services (e.g. `22` SSH, `25` SMTP, `5432` Postgres, `6379` Redis, `8000` FastAPI, `8501` Streamlit, `9222` CDP) are rejected prior to socket connection.

### 2. DNS Resolution & Comprehensive IP Blacklist
Before initiating an outbound socket, the hostname is resolved via `socket.getaddrinfo()`. Every returned IP address (both IPv4 and IPv6) is validated using Python's `ipaddress` library against:
- **Loopback Addresses:** `127.0.0.0/8`, `::1`, `localhost`
- **RFC 1918 Private IPv4 Networks:** `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- **Unique Local IPv6 Networks:** `fc00::/7`
- **Link-Local & Cloud Metadata Endpoints:** `169.254.0.0/16`, `fe80::/10` (specifically AWS/GCP/Azure Instance Metadata Service `169.254.169.254`, Alibaba Cloud `100.100.100.200`, Oracle Cloud `169.254.169.254`)
- **Carrier-Grade NAT (CGNAT):** `100.64.0.0/10`
- **Multicast & Reserved Spaces:** `224.0.0.0/4`, `240.0.0.0/4`, `ff00::/8`, `0.0.0.0/8`

### 3. Redirect Handling & DNS Rebinding Mitigation
- **Controlled Redirects:** Requests are executed with `allow_redirects=False`. If a redirect (301, 302, 307, 308) is returned, the target `Location` header is extracted, re-parsed, and passed through the complete DNS resolution and SSRF filter before being fetched (maximum 3 hops).
- **DNS Rebinding Protection:** The IP address validated during DNS resolution is pinned, or the IP is resolved immediately before socket connection. If a hostname resolves to both a public and a private IP, it is immediately rejected.

### 4. Timeouts & Response Size Guardrails
- **Timeouts:** Connect timeout capped at 4.0 seconds, read timeout capped at 6.0 seconds (total request time $\le 10.0$ seconds).
- **Response Size Limit:** Responses are read in streaming chunks (8 KB). If the cumulative payload exceeds `2.5 MB` (`2,621,440 bytes`), the connection is terminated immediately, preventing memory exhaustion or zip-bomb style attacks.
- **Ethical Compliance:** The fetcher uses standard polite User-Agent headers, respects HTTP 403/429 status codes, and **never attempts CAPTCHA solving, credential spoofing, or authentication bypass**.

---

## 4. Company Data Accuracy & Anti-Hallucination Safeguards

Job seekers depend on accurate data when targeting company positions. Automated extraction must never invent or assume company facts:

1. **Zero Fabrication of Company Profiles:**
   - The system will **never** invent company technology stacks, hiring quotas, open vacancies, preferred qualifications, or corporate policies.
   - All extracted attributes (Company Name, Job Title, Experience, Education, Mandatory Skills, Preferred Skills) must be grounded in direct textual evidence parsed from the target source.
2. **Clear Separation of Extracted vs. Inferred Data:**
   - In the UI and data structures, fields are strictly partitioned:
     - `extracted_skills`: Explicit technical skills named in the posting.
     - `inferred_domain_context`: Canonical category groupings (e.g. mapping `React` to `Frontend Engineering`), explicitly flagged with a visual tag `[Inferred Category]`.
     - `confidence_score` / `source_attribution`: Highlights the origin of the data (*"Direct Job Description Text"* vs. *"Canonical Skill Match"*).
3. **Graceful Fallback on Gated or Inaccessible Pages:**
   - For protected job portals (e.g., LinkedIn login gates, Workday authentication, anti-bot Cloudflare challenges), the fetcher will not guess or claim successful extraction.
   - It immediately renders an informative alert:  
     *"This job page requires authentication or has restricted automated access. Please copy and paste the job description text into the Manual Job Description tab below."*

---

## 5. Resume Improvement Safety & Ethics

Career guidance must enhance candidate presentation without falsifying records:

1. **Strict Prohibition on Fabricated Credentials:**
   - The resume improver will **never** invent or suggest adding:
     - Fake companies or employment dates
     - Fabricated percentages or metrics (e.g. *"Increased revenue by 42%"*)
     - Unearned degrees or certifications
     - Unverified technical tools not confirmed by the candidate
2. **Evidence-Based Framing via Structured Templates:**
   - Suggestions focus exclusively on **reframing genuine experiences** using the Google XYZ formula:  
     *Accomplished [X] as measured by [Y] by doing [Z].*
   - When metrics are missing, the tool provides **bracketed placeholders** prompting the candidate to quantify their own real achievements (e.g., *"Engineered REST APIs using FastAPI, reducing response latency by [insert measured % or ms if tracked]"*).
3. **Keyword Alignment & Omission Highlighting:**
   - The tool cross-references the candidate's confirmed skills against the job posting's mandatory requirements.
   - If the candidate mentioned a tool in their project bullets (e.g., Docker) but omitted it from their Skills summary, the tool suggests adding it to their technical summary.

---

## 6. Regression Protection Confirmation

| Platform Subsystem | Current State | Protection Strategy During Phase 2 | Status |
| :--- | :--- | :--- | :---: |
| **All 8 Dashboard Pages** | Operational (`overview`, `job_market`, `salary_analytics`, `salary_prediction`, `resume_analyzer`, `skill_gap`, `data_quality`, `about`) | No existing page files will be modified. The new page `company_intelligence.py` is a standalone 9th page. | Confirmed Untouched |
| **Salary Prediction ML Engine** | Primary Gradient Boosting ($R^2=0.96$) & Secondary XGBoost ($R^2=0.96$) | Models, preprocessors, 72-dimension feature pipelines (`models/`), and inference modules (`src/salary_model.py`) remain completely untouched. | Confirmed Untouched |
| **Resume Parser & Skill Analyzer** | Curated regex taxonomy (42 skills), in-memory PDF extraction, market skill gap scoring | Existing modules (`src/resume_parser.py`, `src/skill_analyzer.py`) remain untouched; their public functions are imported and reused as read-only dependencies. | Confirmed Untouched |
| **Database Tables & Schema** | 4 tables (`companies`, `skills`, `job_postings`, `job_skills`) in SQLite (`data/job_market.db`) | Zero schema changes, zero migrations. The new feature operates statelessly in session memory. | Confirmed Untouched |
| **FastAPI REST API** | 9 application endpoints + 4 OpenAPI documentation endpoints | All existing paths, parameters, schemas, and return formats remain unchanged. | Confirmed Untouched |
| **Automated Test Baseline** | 86 unit and integration tests passing in 15s | All 86 tests must continue to pass. ~25 new tests in `tests/test_company_intelligence.py` will increase the test count to $\ge 110$. | Confirmed Untouched |

---

## 7. Proposed Package Structure (Phase 2)

```text
src/company_intelligence/
├── __init__.py                  # Package exports & versioning
├── validators.py                # Strict SSRF validation (ipaddress checks, port/scheme limits)
├── job_extractor.py             # Safe streaming HTTP fetching with size limits & LinkedIn fallback
├── requirement_parser.py        # Structured parser (Mandatory/Preferred, Experience, Education)
├── company_analyzer.py          # Company tech stack & requirement aggregator
├── candidate_comparator.py      # Candidate vs Job matching matrix (transparent 70/30 formula)
├── recommendation_engine.py     # Skill remediation guidance grouped by High, Medium, Low priority
├── resume_improver.py           # Job-specific resume bullet enhancements (zero hallucinated credentials)
└── roadmap_generator.py         # 30-day, 60-day, and 90-day actionable career progress roadmaps

dashboard/pages/
└── company_intelligence.py      # New 9th page with 7 UI sections in NIRNAYA purple and orange

tests/
└── test_company_intelligence.py # ~25 comprehensive unit & integration tests

reports/
└── company_intelligence_report.md # Verification artifact, test evidence, and architecture documentation
```

### Minimal Additive Edits to Existing Files
1. [`dashboard/components/sidebar.py`](file:///c:/Users/LENOVO/OneDrive/Desktop/Applet%20logic/Data%20Science/india_job_market_internship_dataset/project_anti/dashboard/components/sidebar.py):
   - Add `"Company Intelligence"` to `NAVIGATION_PAGES`.
   - Add `"Company Intelligence": "🏢"` to `NAVIGATION_ICONS`.
2. [`dashboard/app.py`](file:///c:/Users/LENOVO/OneDrive/Desktop/Applet%20logic/Data%20Science/india_job_market_internship_dataset/project_anti/dashboard/app.py):
   - Add `from dashboard.pages.company_intelligence import render_company_intelligence_page`.
   - Add `elif selected_page == "Company Intelligence": render_company_intelligence_page()`.
3. [`tests/test_dashboard.py`](file:///c:/Users/LENOVO/OneDrive/Desktop/Applet%20logic/Data%20Science/india_job_market_internship_dataset/project_anti/tests/test_dashboard.py):
   - Add assertion verifying `render_company_intelligence_page` exists and can be imported.

---

## 8. Final Approval Gate

Phase 1 safety review and reconciliation are complete.  
**No application code or new files have been written.**

Please review this safety plan. Once approved, Phase 2 implementation will commence immediately.
