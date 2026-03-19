import contextlib
import logging
import os

from dotenv import load_dotenv
from psycopg2 import Error as PsycopgError, pool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

load_dotenv()

_pool = None


def _get_database_url() -> str:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("Missing DATABASE_URL in environment")
    return database_url


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(1, 10, _get_database_url())
    return _pool


@contextlib.contextmanager
def get_db():
    """
    Yields a connection cursor from the pool.
    Handles transaction commit/rollback automatically.
    """
    conn = None
    current_pool = _get_pool()
    try:
        conn = current_pool.getconn()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                yield cur
    except PsycopgError as exc:
        logger.error("Database error: %s", exc)
        raise
    finally:
        if conn:
            current_pool.putconn(conn)


def close_pool():
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
