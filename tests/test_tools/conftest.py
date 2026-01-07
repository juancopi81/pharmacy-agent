"""Shared fixtures for tool tests."""

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest


def create_test_schema(conn: sqlite3.Connection) -> None:
    """Create database schema for testing."""
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


def seed_test_data(conn: sqlite3.Connection) -> None:
    """Seed test data."""
    # Users
    users = [
        (1, "David Cohen", "050-1234567", "david.cohen@example.com"),
        (2, "Sarah Levi", "052-2345678", "sarah.levi@example.com"),
        (3, "Michael Ben-Ari", "054-3456789", "michael.benari@example.com"),
    ]
    conn.executemany(
        "INSERT INTO users (user_id, name, phone, email) VALUES (?, ?, ?, ?)",
        users,
    )

    # Medications
    medications = [
        (
            1,
            "Ibuprofen",
            "איבופרופן",
            "Ibuprofen",
            "Take 200-400mg every 4-6 hours as needed.",
            "קח 200-400 מ״ג כל 4-6 שעות לפי הצורך.",
            0,
            "Do not use if allergic to NSAIDs.",
            "אין להשתמש אם יש רגישות לתרופות נוגדות דלקת.",
        ),
        (
            2,
            "Amoxicillin",
            "אמוקסיצילין",
            "Amoxicillin (as trihydrate)",
            "Take 500mg every 8 hours for 7-10 days.",
            "קח 500 מ״ג כל 8 שעות למשך 7-10 ימים.",
            1,
            "May cause allergic reactions.",
            "עלול לגרום לתגובות אלרגיות.",
        ),
        (
            3,
            "Cetirizine",
            "צטיריזין",
            "Cetirizine hydrochloride",
            "Take 10mg once daily.",
            "קח 10 מ״ג פעם ביום.",
            0,
            "Avoid driving if drowsy.",
            "להימנע מנהיגה אם מרגישים עייפות.",
        ),
    ]
    conn.executemany(
        """INSERT INTO medications
           (med_id, name_en, name_he, active_ingredients, dosage_en, dosage_he,
            rx_required, warnings_en, warnings_he)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        medications,
    )

    # Prescriptions
    prescriptions = [
        (1, 1, 2, 2, "active"),  # David - Amoxicillin, 2 refills
        (2, 1, 1, 0, "completed"),  # David - Ibuprofen, no refills, completed
        (3, 2, 2, 0, "completed"),  # Sarah - Amoxicillin, no refills
        (4, 3, 2, 3, "active"),  # Michael - Amoxicillin, 3 refills
        (5, 2, 1, 0, "expired"),  # Sarah - Ibuprofen, expired
    ]
    conn.executemany(
        """INSERT INTO prescriptions
           (presc_id, user_id, med_id, refills_left, status)
           VALUES (?, ?, ?, ?, ?)""",
        prescriptions,
    )

    # Inventory
    inventory = [
        (1, 1, 150, None),  # Ibuprofen - in stock
        (1, 2, 0, "2025-01-15"),  # Amoxicillin - out of stock, ETA
        (1, 3, 200, None),  # Cetirizine - in stock
    ]
    conn.executemany(
        """INSERT INTO inventory
           (store_id, med_id, qty, restock_eta)
           VALUES (?, ?, ?, ?)""",
        inventory,
    )


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database with seeded data."""
    # Create temp file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Create and seed database
    conn = sqlite3.connect(db_path)
    try:
        create_test_schema(conn)
        seed_test_data(conn)
        conn.commit()
    finally:
        conn.close()

    # Set environment variable for database path
    old_db_path = os.environ.get("DB_PATH")
    os.environ["DB_PATH"] = db_path

    # Clear cached settings to pick up new DB_PATH
    from apps.api.config import get_settings

    get_settings.cache_clear()

    yield db_path

    # Cleanup
    if old_db_path:
        os.environ["DB_PATH"] = old_db_path
    else:
        os.environ.pop("DB_PATH", None)

    get_settings.cache_clear()

    # Remove temp database
    Path(db_path).unlink(missing_ok=True)
