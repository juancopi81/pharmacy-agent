"""Database connection helpers for async SQLite access."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite

from apps.api.config import get_settings


def get_db_path() -> Path:
    """Get database path from config."""
    settings = get_settings()
    return Path(settings.db_path)


@asynccontextmanager
async def get_connection() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Async context manager for database connections.

    Enables foreign key constraints and returns row results as sqlite3.Row
    for dict-like access.

    Usage:
        async with get_connection() as db:
            async with db.execute("SELECT * FROM users") as cursor:
                rows = await cursor.fetchall()
    """
    db_path = get_db_path()
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        db.row_factory = aiosqlite.Row
        yield db
