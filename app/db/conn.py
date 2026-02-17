import os
import contextlib
import logging
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

# Setup logger
logger = logging.getLogger(__name__)

# Load DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL in environment")

# Initialize connection pool
# min=1, max=10 connections
_pool = pool.SimpleConnectionPool(1, 10, DATABASE_URL)

@contextlib.contextmanager
def get_db():
    """
    Yields a connection cursor from the pool.
    Handles transaction commit/rollback automatically.
    """
    conn = None
    try:
        conn = _pool.getconn()
        with conn:  # starts transaction
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                yield cur
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            _pool.putconn(conn)

def close_pool():
    if _pool:
        _pool.closeall()
