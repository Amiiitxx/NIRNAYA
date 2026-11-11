"""
Test PostgreSQL connection using credentials from .env
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
user = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "postgres")
pwd = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "postgres")
host = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432")
dbname = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "job_market_db")

print(f"Connecting to host={host}, port={port}, user={user}...")
try:
    conn = psycopg2.connect(dbname="postgres", user=user, password=pwd, host=host, port=port, connect_timeout=5)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT version();")
    ver = cur.fetchone()[0]
    print(f"Connected to PostgreSQL successfully! Version: {ver}")

    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{dbname}';")
    exists = cur.fetchone()
    if not exists:
        print(f"Database '{dbname}' does not exist yet. Creating...")
        cur.execute(f"CREATE DATABASE {dbname};")
        print(f"Database '{dbname}' created successfully.")
    else:
        print(f"Database '{dbname}' already exists.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"PostgreSQL connection error: {e}")

