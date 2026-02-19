from app.db.conn import get_db

def add_reminded_column():
    with get_db() as cur:
        try:
            cur.execute("ALTER TABLE bookings ADD COLUMN reminded BOOLEAN NOT NULL DEFAULT FALSE;")
            print("Successfully added 'reminded' column to 'bookings' table.")
        except Exception as e:
            if "already exists" in str(e):
                print("Column 'reminded' already exists.")
            else:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_reminded_column()
