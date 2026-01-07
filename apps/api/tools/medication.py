"""Medication lookup tool for the pharmacy agent."""

from langchain_core.tools import tool

from apps.api.database import get_connection
from apps.api.logging_config import get_logger
from apps.api.tools.exceptions import ToolError
from apps.api.tools.schemas import MedicationInfo, MedicationResult, ToolErrorCode

logger = get_logger(__name__)


async def _search_medications(query: str) -> list[dict]:
    """
    Search medications by name (EN or HE).

    Tries exact match first, then partial match.
    English: case-insensitive
    Hebrew: direct match (no LOWER)
    """
    query = query.strip()
    if not query:
        return []

    async with get_connection() as db:
        # Try exact match first (EN case-insensitive, HE direct)
        async with db.execute(
            """
            SELECT * FROM medications
            WHERE LOWER(name_en) = LOWER(?) OR name_he = ?
            """,
            (query, query),
        ) as cursor:
            rows = await cursor.fetchall()
            if rows:
                return [dict(row) for row in rows]

        # Fallback to partial match
        pattern = f"%{query}%"
        async with db.execute(
            """
            SELECT * FROM medications
            WHERE LOWER(name_en) LIKE LOWER(?) OR name_he LIKE ?
            """,
            (pattern, pattern),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


def _row_to_medication_info(row: dict) -> MedicationInfo:
    """Convert database row to MedicationInfo."""
    return MedicationInfo(
        med_id=row["med_id"],
        name_en=row["name_en"],
        name_he=row["name_he"],
        active_ingredients=row["active_ingredients"] or "",
        dosage_en=row["dosage_en"] or "",
        dosage_he=row["dosage_he"] or "",
        rx_required=bool(row["rx_required"]),
        warnings_en=row["warnings_en"] or "",
        warnings_he=row["warnings_he"] or "",
    )


@tool
async def get_medication_by_name(medication_name: str) -> dict:
    """
    Look up medication information by name (English or Hebrew).

    Use this tool when the user asks about a specific medication's
    ingredients, dosage, warnings, or prescription requirements.

    Args:
        medication_name: The name of the medication to search for
                        (can be in English or Hebrew, partial matches allowed)

    Returns:
        dict with medication details including active ingredients,
        dosage instructions, warnings, and whether prescription is required.
    """
    logger.info(f"get_medication_by_name called with: {medication_name}")

    query = medication_name.strip()
    if not query:
        error = ToolError(
            ToolErrorCode.NOT_FOUND,
            "Medication name cannot be empty",
        )
        logger.info(f"get_medication_by_name error: {error.code.value}")
        return error.to_dict()

    try:
        matches = await _search_medications(query)

        if len(matches) == 0:
            error = ToolError(
                ToolErrorCode.NOT_FOUND,
                f"No medication found matching '{query}'",
            )
            logger.info(f"get_medication_by_name result: NOT_FOUND for '{query}'")
            result = error.to_dict()
            result["query"] = query
            return result

        if len(matches) == 1:
            medication = _row_to_medication_info(matches[0])
            logger.info(
                f"get_medication_by_name result: success, med_id={medication.med_id}"
            )
            return MedicationResult(
                success=True,
                medication=medication,
            ).model_dump()

        # Multiple matches - ambiguous
        suggestions = [f"{m['name_en']} ({m['name_he']})" for m in matches]
        error = ToolError(
            ToolErrorCode.AMBIGUOUS,
            f"Multiple medications match '{query}'. Please specify which one.",
            suggestions=suggestions,
        )
        logger.info(f"get_medication_by_name result: AMBIGUOUS, {len(matches)} matches")
        result = error.to_dict()
        result["query"] = query
        return result

    except Exception as e:
        logger.error(f"get_medication_by_name internal error: {e}")
        error = ToolError(
            ToolErrorCode.INTERNAL,
            "An internal error occurred while looking up the medication",
        )
        return error.to_dict()
