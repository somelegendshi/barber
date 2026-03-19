from dotenv import load_dotenv

from app.db.repository import sync_core_id_sequences
from app.scripts.init_db import initialize_production_db


def fix_sequences():
    load_dotenv()
    initialize_production_db()
    sync_core_id_sequences()
    print("All core ID sequences are synchronized.")


if __name__ == "__main__":
    try:
        fix_sequences()
    except Exception as exc:
        print(f"Error: {exc}")
