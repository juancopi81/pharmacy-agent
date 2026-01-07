"""
Database seed script for Pharmacy Agent MVP.

Creates SQLite schema and populates with sample data:
- 10 users
- 5 medications (Hebrew + English)
- Sample prescriptions
- Inventory with varied stock levels

Run: uv run python scripts/seed_db.py
"""

import sqlite3
from pathlib import Path

# Database path (relative to project root)
DB_PATH = Path(__file__).parent.parent / "data" / "pharmacy.db"


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all tables with constraints and indexes."""
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT UNIQUE,
            email TEXT UNIQUE
        );

        CREATE TABLE IF NOT EXISTS medications (
            med_id INTEGER PRIMARY KEY,
            name_en TEXT NOT NULL,
            name_he TEXT NOT NULL,
            active_ingredients TEXT,
            dosage_en TEXT,
            dosage_he TEXT,
            rx_required INTEGER NOT NULL CHECK (rx_required IN (0,1)),
            warnings_en TEXT,
            warnings_he TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_medications_name_en ON medications(name_en);
        CREATE INDEX IF NOT EXISTS idx_medications_name_he ON medications(name_he);

        CREATE TABLE IF NOT EXISTS prescriptions (
            presc_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            med_id INTEGER NOT NULL,
            refills_left INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (med_id) REFERENCES medications(med_id)
        );
        CREATE INDEX IF NOT EXISTS idx_prescriptions_user_id ON prescriptions(user_id);

        CREATE TABLE IF NOT EXISTS inventory (
            store_id INTEGER NOT NULL DEFAULT 1,
            med_id INTEGER NOT NULL,
            qty INTEGER NOT NULL DEFAULT 0,
            restock_eta TEXT,
            PRIMARY KEY (store_id, med_id),
            FOREIGN KEY (med_id) REFERENCES medications(med_id)
        );
    """
    )


def seed_users(conn: sqlite3.Connection) -> None:
    """Seed 10 sample users."""
    users = [
        (1, "David Cohen", "050-1234567", "david.cohen@example.com"),
        (2, "Sarah Levi", "052-2345678", "sarah.levi@example.com"),
        (3, "Michael Ben-Ari", "054-3456789", "michael.benari@example.com"),
        (4, "Rachel Mizrachi", "050-4567890", "rachel.m@example.com"),
        (5, "Yossi Goldstein", "052-5678901", "yossi.g@example.com"),
        (6, "Noa Shapiro", "054-6789012", "noa.shapiro@example.com"),
        (7, "Amit Peretz", "050-7890123", "amit.peretz@example.com"),
        (8, "Maya Friedman", "052-8901234", "maya.f@example.com"),
        (9, "Eyal Katz", "054-9012345", "eyal.katz@example.com"),
        (10, "Tamar Rosenberg", "050-0123456", "tamar.r@example.com"),
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO users (user_id, name, phone, email) VALUES (?, ?, ?, ?)",
        users,
    )


def seed_medications(conn: sqlite3.Connection) -> None:
    """Seed 5 medications with Hebrew and English info."""
    medications = [
        # (med_id, name_en, name_he, active_ingredients, dosage_en, dosage_he,
        #  rx_required, warnings_en, warnings_he)
        (
            1,
            "Ibuprofen",
            "איבופרופן",
            "Ibuprofen",
            "Take 200-400mg every 4-6 hours as needed. Max 1200mg/day.",
            "קח 200-400 מ״ג כל 4-6 שעות לפי הצורך. מקסימום 1200 מ״ג ליום.",
            0,  # OTC
            "Do not use if allergic to NSAIDs. Avoid with stomach ulcers.",
            "אין להשתמש אם יש רגישות לתרופות נוגדות דלקת. להימנע בכיב קיבה.",
        ),
        (
            2,
            "Amoxicillin",
            "אמוקסיצילין",
            "Amoxicillin (as trihydrate)",
            "Take 500mg every 8 hours for 7-10 days. Complete full course.",
            "קח 500 מ״ג כל 8 שעות למשך 7-10 ימים. יש להשלים את כל הקורס.",
            1,  # Rx required
            "May cause allergic reactions. Inform doctor of penicillin allergy.",
            "עלול לגרום לתגובות אלרגיות. יש ליידע את הרופא על רגישות לפניצילין.",
        ),
        (
            3,
            "Omeprazole",
            "אומפרזול",
            "Omeprazole",
            "Take 20mg once daily before breakfast for 4-8 weeks.",
            "קח 20 מ״ג פעם ביום לפני ארוחת בוקר למשך 4-8 שבועות.",
            0,  # OTC
            "Long-term use may affect calcium absorption. Consult doctor for prolonged use.",
            "שימוש ממושך עלול להשפיע על ספיגת סידן. יש להתייעץ עם רופא לשימוש ממושך.",
        ),
        (
            4,
            "Metformin",
            "מטפורמין",
            "Metformin hydrochloride",
            "Start 500mg twice daily with meals. May increase to 2000mg/day.",
            "התחל 500 מ״ג פעמיים ביום עם ארוחות. ניתן להעלות עד 2000 מ״ג ליום.",
            1,  # Rx required
            "Take with food to reduce stomach upset. Avoid alcohol.",
            "יש לקחת עם אוכל למניעת בעיות קיבה. להימנע מאלכוהול.",
        ),
        (
            5,
            "Cetirizine",
            "צטיריזין",
            "Cetirizine hydrochloride",
            "Take 10mg once daily. May cause drowsiness.",
            "קח 10 מ״ג פעם ביום. עלול לגרום לנמנום.",
            0,  # OTC
            "Avoid driving if drowsy. Do not exceed recommended dose.",
            "להימנע מנהיגה אם מרגישים עייפות. אין לחרוג מהמינון המומלץ.",
        ),
    ]
    conn.executemany(
        """INSERT OR REPLACE INTO medications
           (med_id, name_en, name_he, active_ingredients, dosage_en, dosage_he,
            rx_required, warnings_en, warnings_he)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        medications,
    )


def seed_prescriptions(conn: sqlite3.Connection) -> None:
    """Seed sample prescriptions with varied scenarios."""
    prescriptions = [
        # (presc_id, user_id, med_id, refills_left, status)
        (1, 1, 2, 2, "active"),  # David - Amoxicillin, 2 refills
        (2, 1, 4, 5, "active"),  # David - Metformin, 5 refills
        (3, 2, 2, 0, "completed"),  # Sarah - Amoxicillin, no refills
        (4, 3, 4, 3, "active"),  # Michael - Metformin, 3 refills
        (5, 4, 2, 1, "active"),  # Rachel - Amoxicillin, 1 refill
        (6, 5, 4, 0, "expired"),  # Yossi - Metformin, expired
        (7, 6, 2, 4, "active"),  # Noa - Amoxicillin, 4 refills
        (8, 7, 4, 2, "active"),  # Amit - Metformin, 2 refills
    ]
    conn.executemany(
        """INSERT OR REPLACE INTO prescriptions
           (presc_id, user_id, med_id, refills_left, status)
           VALUES (?, ?, ?, ?, ?)""",
        prescriptions,
    )


def seed_inventory(conn: sqlite3.Connection) -> None:
    """Seed inventory with varied stock levels."""
    inventory = [
        # (store_id, med_id, qty, restock_eta)
        (1, 1, 150, None),  # Ibuprofen - in stock
        (1, 2, 0, "2025-01-15"),  # Amoxicillin - out of stock, ETA
        (1, 3, 75, None),  # Omeprazole - in stock
        (1, 4, 5, "2025-01-10"),  # Metformin - low stock, ETA
        (1, 5, 200, None),  # Cetirizine - in stock
    ]
    conn.executemany(
        """INSERT OR REPLACE INTO inventory
           (store_id, med_id, qty, restock_eta)
           VALUES (?, ?, ?, ?)""",
        inventory,
    )


def main() -> None:
    """Create database, schema, and seed data."""
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database for clean seed
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing database: {DB_PATH}")

    # Connect and seed
    conn = sqlite3.connect(DB_PATH)
    try:
        create_schema(conn)
        print("Schema created.")

        seed_users(conn)
        print("Seeded 10 users.")

        seed_medications(conn)
        print("Seeded 5 medications.")

        seed_prescriptions(conn)
        print("Seeded 8 prescriptions.")

        seed_inventory(conn)
        print("Seeded inventory for 5 medications.")

        conn.commit()
        print(f"\nDatabase created successfully: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
