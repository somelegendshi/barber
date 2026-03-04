import logging
from app.db.conn import get_db

logger = logging.getLogger(__name__)

def migrate_reminders():
    """
    Checks if 'reminded' column exists in bookings table.
    If not, adds it.
    """
    try:
        with get_db() as cur:
            # Check if column exists
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='bookings' AND column_name='reminded';
            """)
            if not cur.fetchone():
                logger.info("⚙️ Applying migration: Adding 'reminded' column to bookings...")
                cur.execute("ALTER TABLE bookings ADD COLUMN reminded BOOLEAN NOT NULL DEFAULT FALSE;")
                logger.info("✅ Migration successful.")
            else:
                logger.info("✅ Schema check: 'reminded' column exists.")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_reminders()