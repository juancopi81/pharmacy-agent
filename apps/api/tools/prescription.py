"""Prescription management tool for the pharmacy agent."""

from langchain_core.tools import tool

from apps.api.database import get_connection
from apps.api.logging_config import get_logger
from apps.api.tools.exceptions import ToolError
from apps.api.tools.schemas import (
    PrescriptionAction,
    PrescriptionInfo,
    PrescriptionListResult,
    PrescriptionStatus,
    RefillStatusResult,
    ToolErrorCode,
)

logger = get_logger(__name__)


async def _lookup_user(identifier: str) -> dict | None:
    """Look up user by email or phone."""
    identifier = identifier.strip()
    if not identifier:
        return None

    async with get_connection() as db:
        async with db.execute(
            """
            SELECT user_id, name, phone, email FROM users
            WHERE LOWER(email) = LOWER(?) OR phone = ?
            """,
            (identifier, identifier),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def _get_user_prescriptions(user_id: int) -> list[dict]:
    """Get all prescriptions for a user."""
    async with get_connection() as db:
        async with db.execute(
            """
            SELECT p.presc_id, p.med_id, p.refills_left, p.status,
                   m.name_en, m.name_he
            FROM prescriptions p
            JOIN medications m ON p.med_id = m.med_id
            WHERE p.user_id = ?
            """,
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def _get_prescription_by_id(
    presc_id: int, user_id: int
) -> dict | None:
    """Get a specific prescription ensuring it belongs to the user."""
    async with get_connection() as db:
        async with db.execute(
            """
            SELECT p.presc_id, p.med_id, p.refills_left, p.status,
                   m.name_en, m.name_he
            FROM prescriptions p
            JOIN medications m ON p.med_id = m.med_id
            WHERE p.presc_id = ? AND p.user_id = ?
            """,
            (presc_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


def _row_to_prescription_info(row: dict) -> PrescriptionInfo:
    """Convert database row to PrescriptionInfo."""
    # Normalize status and handle unexpected values safely
    status_raw = str(row["status"] or "").lower()
    try:
        status = PrescriptionStatus(status_raw)
    except ValueError:
        logger.warning(
            f"Unknown prescription status '{row['status']}', defaulting to expired"
        )
        status = PrescriptionStatus.EXPIRED

    can_refill = status == PrescriptionStatus.ACTIVE and row["refills_left"] > 0
    return PrescriptionInfo(
        presc_id=row["presc_id"],
        med_id=row["med_id"],
        medication_name_en=row["name_en"],
        medication_name_he=row["name_he"],
        refills_left=row["refills_left"],
        status=status,
        can_refill=can_refill,
    )


async def _handle_list_action(user: dict) -> dict:
    """Handle LIST action - return all prescriptions for user."""
    prescriptions = await _get_user_prescriptions(user["user_id"])

    prescription_list = [_row_to_prescription_info(p) for p in prescriptions]

    logger.info(
        f"prescription_management LIST: user_id={user['user_id']}, "
        f"count={len(prescription_list)}"
    )

    return PrescriptionListResult(
        success=True,
        user_name=user["name"],
        prescriptions=prescription_list,
    ).model_dump()


async def _handle_refill_status_action(
    user: dict, prescription_id: int | None
) -> dict:
    """Handle REFILL_STATUS action - check refill eligibility."""
    if prescription_id is None:
        error = ToolError(
            ToolErrorCode.NOT_FOUND,
            "prescription_id is required for REFILL_STATUS action",
        )
        return error.to_dict()

    prescription = await _get_prescription_by_id(prescription_id, user["user_id"])

    if not prescription:
        error = ToolError(
            ToolErrorCode.NOT_FOUND,
            f"Prescription {prescription_id} not found for this user",
        )
        logger.info(
            f"prescription_management REFILL_STATUS: "
            f"prescription {prescription_id} not found for user {user['user_id']}"
        )
        return error.to_dict()

    presc_info = _row_to_prescription_info(prescription)

    # Determine eligibility and reason
    if presc_info.status != PrescriptionStatus.ACTIVE:
        refill_eligible = False
        reason = f"Prescription is {presc_info.status.value}"
    elif presc_info.refills_left <= 0:
        refill_eligible = False
        reason = "No refills remaining"
    else:
        refill_eligible = True
        reason = f"{presc_info.refills_left} refill(s) available"

    logger.info(
        f"prescription_management REFILL_STATUS: presc_id={prescription_id}, "
        f"eligible={refill_eligible}, reason={reason}"
    )

    return RefillStatusResult(
        success=True,
        prescription=presc_info,
        refill_eligible=refill_eligible,
        reason=reason,
    ).model_dump()


@tool
async def prescription_management(
    user_identifier: str,
    action: str,
    prescription_id: int | None = None,
) -> dict:
    """
    Manage user prescriptions - list all prescriptions or check refill status.

    Use this tool when users ask about their prescriptions or refills.
    Requires user identification via email or phone number.

    Args:
        user_identifier: User's email address or phone number
        action: Either "LIST" to see all prescriptions, or "REFILL_STATUS"
               to check if a specific prescription can be refilled
        prescription_id: Required for REFILL_STATUS action - the prescription
                        to check

    Returns:
        For LIST: dict with list of all user prescriptions
        For REFILL_STATUS: dict with refill eligibility and remaining refills
    """
    logger.info(
        f"prescription_management called: identifier={user_identifier}, "
        f"action={action}, presc_id={prescription_id}"
    )

    # Validate action
    try:
        action_enum = PrescriptionAction(action.upper())
    except ValueError:
        error = ToolError(
            ToolErrorCode.INVALID_STATE,
            f"Invalid action '{action}'. Must be 'LIST' or 'REFILL_STATUS'",
        )
        return error.to_dict()

    # Look up user
    user = await _lookup_user(user_identifier)
    if not user:
        error = ToolError(
            ToolErrorCode.UNAUTHORIZED,
            f"User not found with identifier: {user_identifier}",
        )
        logger.info(
            f"prescription_management error: user not found: {user_identifier}"
        )
        return error.to_dict()

    try:
        if action_enum == PrescriptionAction.LIST:
            return await _handle_list_action(user)
        else:  # REFILL_STATUS
            return await _handle_refill_status_action(user, prescription_id)

    except Exception as e:
        logger.error(f"prescription_management internal error: {e}")
        error = ToolError(
            ToolErrorCode.INTERNAL,
            "An internal error occurred while managing prescriptions",
        )
        return error.to_dict()
