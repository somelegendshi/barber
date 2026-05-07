import os
import sys

from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../.."))
load_dotenv()

from app.db.conn import get_db

MIGRATION_LOCK_KEY = 9021450


def _column_exists(cur, table_name: str, column_name: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        LIMIT 1
        """,
        (table_name, column_name),
    )
    return cur.fetchone() is not None


def _sequence_exists(cur, sequence_name: str) -> bool:
    cur.execute("SELECT to_regclass(%s) AS seq_name", (sequence_name,))
    row = cur.fetchone()
    return bool(row and row["seq_name"])


def _sync_named_sequence(cur, sequence_name: str, max_value: int) -> None:
    if max_value > 0:
        cur.execute("SELECT setval(%s::regclass, %s, true)", (sequence_name, max_value))
    else:
        cur.execute("SELECT setval(%s::regclass, %s, false)", (sequence_name, 1))


def _sync_table_id_sequence(cur, table_name: str) -> None:
    cur.execute(f"SELECT COALESCE(MAX(id), 0) AS max_id FROM {table_name}")
    max_id = cur.fetchone()["max_id"]
    _sync_named_sequence(cur, f"{table_name}_id_seq", max_id)


def _sync_core_id_sequences(cur) -> None:
    for table_name in ["shops", "barbers", "services", "bookings", "customers", "work_hours", "time_off"]:
        _sync_table_id_sequence(cur, table_name)


def _ensure_shop_public_codes(cur) -> None:
    if not _column_exists(cur, "shops", "public_code"):
        print("Adding shops.public_code ...")
        cur.execute("ALTER TABLE shops ADD COLUMN public_code BIGINT;")

    cur.execute(
        """
        WITH ordered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS code
            FROM shops
            WHERE public_code IS NULL
        )
        UPDATE shops AS s
        SET public_code = ordered.code
        FROM ordered
        WHERE s.id = ordered.id
        """
    )

    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_shops_public_code ON shops (public_code)")

    if not _sequence_exists(cur, "shops_public_code_seq"):
        cur.execute("CREATE SEQUENCE shops_public_code_seq")

    cur.execute("SELECT COALESCE(MAX(public_code), 0) AS max_code FROM shops")
    max_code = cur.fetchone()["max_code"]
    _sync_named_sequence(cur, "shops_public_code_seq", max_code)

    cur.execute(
        """
        ALTER TABLE shops
        ALTER COLUMN public_code SET DEFAULT nextval('shops_public_code_seq')
        """
    )

    cur.execute("SELECT COUNT(*) AS total FROM shops WHERE public_code IS NULL")
    if cur.fetchone()["total"] == 0:
        cur.execute("ALTER TABLE shops ALTER COLUMN public_code SET NOT NULL")


def initialize_production_db():
    print("Running database migrations...")
    schema_path = os.path.join(current_dir, "../db/schema.sql")

    try:
        with get_db() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (MIGRATION_LOCK_KEY,))

            with open(schema_path, "r", encoding="utf-8") as f:
                cur.execute(f.read())

            if not _column_exists(cur, "customers", "username"):
                print("Adding customers.username ...")
                cur.execute("ALTER TABLE customers ADD COLUMN username TEXT;")

            _ensure_shop_public_codes(cur)

            if not _column_exists(cur, "customers", "language_code"):
                print("Adding customers.language_code ...")
                cur.execute(
                    "ALTER TABLE customers ADD COLUMN language_code TEXT "
                    "CHECK (language_code IN ('uz', 'ru'));"
                )

            if not _column_exists(cur, "barbers", "telegram_id"):
                print("Adding barbers.telegram_id ...")
                cur.execute("ALTER TABLE barbers ADD COLUMN telegram_id BIGINT;")

            if not _column_exists(cur, "barbers", "notify_telegram_id"):
                print("Adding barbers.notify_telegram_id ...")
                cur.execute("ALTER TABLE barbers ADD COLUMN notify_telegram_id BIGINT;")

            cur.execute(
                """
                INSERT INTO shop_admins (shop_id, telegram_id, role)
                SELECT DISTINCT shop_id, telegram_id, 'admin'
                FROM barbers
                WHERE telegram_id IS NOT NULL
                ON CONFLICT (shop_id, telegram_id) DO NOTHING
                """
            )

            if not _column_exists(cur, "bookings", "reminded"):
                print("Adding bookings.reminded ...")
                cur.execute("ALTER TABLE bookings ADD COLUMN reminded BOOLEAN NOT NULL DEFAULT FALSE;")

            cur.execute(
                """
                SELECT telegram_id
                FROM barbers
                WHERE telegram_id IS NOT NULL
                GROUP BY telegram_id
                HAVING COUNT(*) > 1
                LIMIT 1
                """
            )
            duplicate_row = cur.fetchone()
            if duplicate_row:
                print(
                    f"Skipping unique Telegram index because duplicate barber.telegram_id "
                    f"exists: {duplicate_row['telegram_id']}"
                )
            else:
                cur.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_barbers_telegram_id
                    ON barbers (telegram_id)
                    WHERE telegram_id IS NOT NULL
                    """
                )

            _sync_core_id_sequences(cur)

            print("Database is up to date.")
    except Exception as e:
        print(f"Migration Failed: {e}")
        raise


if __name__ == "__main__":
    initialize_production_db()
