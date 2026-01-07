"""Inventory check tool for the pharmacy agent."""

from langchain_core.tools import tool

from apps.api.database import get_connection
from apps.api.logging_config import get_logger
from apps.api.tools.exceptions import ToolError
from apps.api.tools.schemas import InventoryInfo, InventoryResult, ToolErrorCode

logger = get_logger(__name__)


async def _resolve_medication_id(medication_name: str) -> int | None:
    """Resolve medication name to ID (internal helper)."""
    query = medication_name.strip()
    if not query:
        return None

    async with get_connection() as db:
        # Try exact match first
        async with db.execute(
            """
            SELECT med_id FROM medications
            WHERE LOWER(name_en) = LOWER(?) OR name_he = ?
            """,
            (query, query),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return row["med_id"]

        # Fallback to partial match (return first match)
        pattern = f"%{query}%"
        async with db.execute(
            """
            SELECT med_id FROM medications
            WHERE LOWER(name_en) LIKE LOWER(?) OR name_he LIKE ?
            LIMIT 1
            """,
            (pattern, pattern),
        ) as cursor:
            row = await cursor.fetchone()
            return row["med_id"] if row else None


@tool
async def check_inventory(
    medication_id: int | None = None,
    medication_name: str | None = None,
    store_id: int = 1,
) -> dict:
    """
    Check if a medication is in stock at the pharmacy.

    Use this tool when the user asks about medication availability.
    Provide either medication_id (if known from previous lookup) or
    medication_name (will be resolved automatically).

    Args:
        medication_id: The medication ID (from get_medication_by_name result)
        medication_name: The medication name (alternative to medication_id)
        store_id: Store ID to check inventory for (default: 1)

    Returns:
        dict with availability status including in_stock, qty (if available),
        and restock_eta (if out of stock).
    """
    logger.info(
        f"check_inventory called: med_id={medication_id}, "
        f"med_name={medication_name}, store_id={store_id}"
    )

    # Validate input
    if medication_id is None and medication_name is None:
        error = ToolError(
            ToolErrorCode.INVALID_STATE,
            "Either medication_id or medication_name must be provided",
        )
        logger.info("check_inventory error: no identifier provided")
        return error.to_dict()

    # Resolve medication_id if needed (prefer id if both given)
    med_id = medication_id
    if med_id is None and medication_name:
        med_id = await _resolve_medication_id(medication_name)
        if med_id is None:
            error = ToolError(
                ToolErrorCode.NOT_FOUND,
                f"Medication '{medication_name}' not found",
            )
            logger.info(f"check_inventory error: medication not found: {medication_name}")
            return error.to_dict()

    try:
        async with get_connection() as db:
            async with db.execute(
                """
                SELECT i.store_id, i.med_id, i.qty, i.restock_eta,
                       m.name_en, m.name_he
                FROM inventory i
                JOIN medications m ON i.med_id = m.med_id
                WHERE i.med_id = ? AND i.store_id = ?
                """,
                (med_id, store_id),
            ) as cursor:
                row = await cursor.fetchone()

                if not row:
                    error = ToolError(
                        ToolErrorCode.NOT_FOUND,
                        f"No inventory record found for medication ID {med_id} "
                        f"at store {store_id}",
                    )
                    logger.info(
                        f"check_inventory error: no inventory for med_id={med_id}"
                    )
                    return error.to_dict()

                qty = row["qty"]
                in_stock = qty > 0

                inventory = InventoryInfo(
                    med_id=row["med_id"],
                    store_id=row["store_id"],
                    medication_name_en=row["name_en"],
                    medication_name_he=row["name_he"],
                    in_stock=in_stock,
                    qty=qty if in_stock else None,
                    restock_eta=row["restock_eta"] if not in_stock else None,
                )

                logger.info(
                    f"check_inventory result: med_id={med_id}, "
                    f"in_stock={in_stock}, qty={qty}"
                )

                return InventoryResult(
                    success=True,
                    inventory=inventory,
                ).model_dump()

    except Exception as e:
        logger.error(f"check_inventory internal error: {e}")
        error = ToolError(
            ToolErrorCode.INTERNAL,
            "An internal error occurred while checking inventory",
        )
        return error.to_dict()
