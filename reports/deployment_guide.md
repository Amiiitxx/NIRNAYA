# Production Deployment & Operations Guide
## AI-Powered Job Market Intelligence & Salary Prediction System

**Document Version:** 1.0.0  
**Target Environment:** Linux / Docker / Cloud VM / Cloud PaaS  

---

## 1. Recommended Deployment Architecture

For production hosting, the system can be deployed using a containerized microservice pattern or a single-host cloud VM.

```
       [ Client Browser / HTTPS ]
                    |
            [ NGINX / Cloudflare ]
           /                      \
  Port 8501 (Web UI)        Port 8000 (REST API)
          |                          |
 [ Streamlit Container ]    [ FastAPI / Uvicorn ]
          \                          /
           [ SQLAlchemy Data Layer ]
                      |
        [ PostgreSQL 15+ Managed DB ]
```

---

## 2. Environment Variables Configuration

Copy `.env.example` to `.env` and configure appropriate production values:

```bash
# Database Configuration
# For production PostgreSQL:
DATABASE_URL=postgresql+psycopg2://<pg_user>:<pg_password>@<pg_host>:5432/<pg_database>

# Or fallback SQLite:
# DATABASE_URL=sqlite:///./data/job_market.db

# API Service Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=production

# Artifact File Paths (Relative or Absolute)
MODEL_PATH=models/salary_prediction_pipeline.joblib
CLEANED_DATA_PATH=data/processed/cleaned_job_market_all.csv
SALARY_DATA_PATH=data/processed/cleaned_salary_model_data.csv
```

---

## 3. Database Setup & PostgreSQL Configuration

### A. Creating the PostgreSQL Database
Connect to your PostgreSQL server as superuser and execute:
```sql
CREATE USER jobmarket_admin WITH PASSWORD 'secure_production_password';
CREATE DATABASE job_market_db OWNER jobmarket_admin;
GRANT ALL PRIVILEGES ON DATABASE job_market_db TO jobmarket_admin;
```

Update `.env`:
```ini
DATABASE_URL=postgresql+psycopg2://jobmarket_admin:secure_production_password@localhost:5432/job_market_db
```

### B. Ingesting Initial Market Postings
Run the batch ingestion script to build schema tables and load 30,250 records:
```bash
python database/load_data.py
```
*Note: The script is fully idempotent. Re-running it will skip all existing records without throwing errors.*

---

## 4. Application Startup Commands

### A. Running the Streamlit Dashboard
```bash
streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
```

### B. Running the FastAPI REST Microservice
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Interactive Swagger documentation will be accessible at:
`http://<host>:8000/docs`

---

## 5. Docker Deployment

### Dockerfile (Unified Service)
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and artifacts
COPY . .

EXPOSE 8501 8000

# Default launch command for dashboard
CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
```

---

## 6. Security, Storage & Ephemeral Resume Privacy

1. **Zero Permanent Resume Storage:** The application is architected to process candidate resumes in-memory via PyMuPDF byte buffers. No object storage (S3/GCS) or persistent volumes are required for candidate documents.
2. **Model Artifacts:** Ensure the `models/` directory (containing `best_salary_model.joblib`, `feature_pipeline.joblib`, and `model_metadata.json`) is mounted or bundled in the container image.
3. **CORS & Domain Restrictions:** In `api/main.py`, adjust `allow_origins=["*"]` to your specific production frontend domains in production.

---

## 7. Operational Troubleshooting

| Symptom | Probable Cause | Recommended Fix |
| :--- | :--- | :--- |
| `FATAL: password authentication failed` | Incorrect PostgreSQL credentials in `.env` | Verify DB username/password; database automatically falls back to SQLite (`data/job_market.db`). |
| `Missing artifact: models/...` | Git LFS or missing models directory | Verify `models/best_salary_model.joblib` exists before startup. |
| `Upload file exceeds 10 MB` | User uploaded oversized PDF | Resume parser enforces 10 MB limit; advise user to compress or export text-based PDF. |
| `OCR Limitation Warning` | Scanned image-only PDF | PyMuPDF text layer is empty; advise candidate to use a text-based PDF. |

