import sqlite3

DB_NAME = "airline_booking.db"


def get_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        print("Database connection error:", e)
        return None


def create_tables():
    conn = get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        # ---------------- USERS TABLE ----------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)

        # ---------------- FLIGHTS TABLE ----------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
            airline TEXT CHECK(airline IN ('Air India', 'Indigo', 'Vistara')) NOT NULL,
            flight_number TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            travel_date DATE NOT NULL,
            departure_time TEXT NOT NULL,
            arrival_time TEXT NOT NULL,
            economy_price INTEGER NOT NULL,
            business_price INTEGER NOT NULL
        )
        """)

        # ---------------- SEATS TABLE ----------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS seats (
            seat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id INTEGER NOT NULL,
            seat_number TEXT NOT NULL,
            class_name TEXT CHECK(class_name IN ('Economy', 'Business')) NOT NULL,
            is_booked INTEGER DEFAULT 0,
            FOREIGN KEY (flight_id) REFERENCES flights(flight_id)
        )
        """)

        # ---------------- BOOKINGS TABLE ----------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,      -- internal row ID
            booking_id TEXT NOT NULL,                  -- transaction ID (same for multiple seats)
            user_id INTEGER NOT NULL,
            flight_id INTEGER NOT NULL,
            seat_id INTEGER NOT NULL,
            travel_date DATE NOT NULL,
            user_email TEXT NOT NULL,
            price INTEGER NOT NULL,
            booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'CONFIRMED',
            payment_done INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (flight_id) REFERENCES flights(flight_id),
            FOREIGN KEY (seat_id) REFERENCES seats(seat_id)
                                                                )
        """)


        conn.commit()
        print("✅ All tables created successfully.")

    except sqlite3.Error as e:
        print("❌ Error creating tables:", e)

    finally:
        conn.close()


# ---------------- RUN ONCE ----------------
if __name__ == "__main__":
    create_tables()
