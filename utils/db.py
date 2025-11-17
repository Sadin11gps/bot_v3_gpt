# utils/db.py
import os
import psycopg2
import logging

logger = logging.getLogger(__name__)

def connect_db():
    """
    PostgreSQL ডাটাবেজের সাথে কানেকশন তৈরি করে।
    DATABASE_URL environment variable ব্যবহার করবে।
    """
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable is not set.")
        return None

    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None
