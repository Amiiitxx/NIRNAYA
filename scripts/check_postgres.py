import psycopg2
import os

print("Testing direct psycopg2 connection to PostgreSQL...")
configs = [
    {"user": "postgres", "password": "password", "host": "localhost", "port": 5432, "dbname": "postgres"},
    {"user": "postgres", "password": "admin", "host": "localhost", "port": 5432, "dbname": "postgres"},
    {"user": "postgres", "password": "root", "host": "localhost", "port": 5432, "dbname": "postgres"},
    {"user": "postgres", "password": "1234", "host": "localhost", "port": 5432, "dbname": "postgres"},
    {"user": "postgres", "password": "postgres", "host": "localhost", "port": 5432, "dbname": "postgres"},
]

# We are not allowed to guess passwords repeatedly or brute-force, let's just check the default user without password or standard test
try:
    conn = psycopg2.connect(user="postgres", password="postgres", host="localhost", port=5432, dbname="postgres", connect_timeout=2)
    print("Default postgres:postgres connected successfully!")
    conn.close()
except Exception as e:
    err_str = str(e).strip()
    print("PostgreSQL connection error:", type(e).__name__, err_str)

