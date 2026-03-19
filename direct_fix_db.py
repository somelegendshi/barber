from dotenv import load_dotenv

from app.db.repository import sync_core_id_sequences
from app.scripts.init_db import initialize_production_db


def fix_sequences_raw():
    load_dotenv()
    initialize_production_db()
    sync_core_id_sequences()
    print("Database migrations and sequences are synchronized.")


if __name__ == "__main__":
    try:
        fix_sequences_raw()
    except Exception as exc:
        print(f"Error fixing database: {exc}")
