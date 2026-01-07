"""Pharmacy Agent Tools for LangGraph integration."""

from apps.api.tools.exceptions import ToolError
from apps.api.tools.inventory import check_inventory
from apps.api.tools.medication import get_medication_by_name
from apps.api.tools.prescription import prescription_management
from apps.api.tools.schemas import (
    InventoryInfo,
    InventoryResult,
    MedicationInfo,
    MedicationResult,
    PrescriptionAction,
    PrescriptionInfo,
    PrescriptionListResult,
    PrescriptionStatus,
    RefillStatusResult,
    ToolErrorCode,
)

# Tools list for LangGraph ToolNode
PHARMACY_TOOLS = [
    get_medication_by_name,
    check_inventory,
    prescription_management,
]

__all__ = [
    # Tools
    "get_medication_by_name",
    "check_inventory",
    "prescription_management",
    "PHARMACY_TOOLS",
    # Schemas
    "ToolErrorCode",
    "MedicationInfo",
    "MedicationResult",
    "InventoryInfo",
    "InventoryResult",
    "PrescriptionAction",
    "PrescriptionStatus",
    "PrescriptionInfo",
    "PrescriptionListResult",
    "RefillStatusResult",
    # Exceptions
    "ToolError",
]
