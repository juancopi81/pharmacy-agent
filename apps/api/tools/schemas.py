"""Pydantic schemas for pharmacy agent tools."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ToolErrorCode(str, Enum):
    """Standardized error codes for all tools."""

    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_STATE = "INVALID_STATE"
    INTERNAL = "INTERNAL"


class PrescriptionAction(str, Enum):
    """Actions available for prescription management."""

    LIST = "LIST"
    REFILL_STATUS = "REFILL_STATUS"


class PrescriptionStatus(str, Enum):
    """Prescription statuses."""

    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


# --- Medication Schemas ---


class MedicationInfo(BaseModel):
    """Medication information returned by get_medication_by_name."""

    med_id: int = Field(..., description="Unique medication identifier")
    name_en: str = Field(..., description="Medication name in English")
    name_he: str = Field(..., description="Medication name in Hebrew")
    active_ingredients: str = Field(..., description="Active ingredients")
    dosage_en: str = Field(..., description="Dosage instructions in English")
    dosage_he: str = Field(..., description="Dosage instructions in Hebrew")
    rx_required: bool = Field(..., description="Whether prescription is required")
    warnings_en: str = Field(..., description="Warnings in English")
    warnings_he: str = Field(..., description="Warnings in Hebrew")


class MedicationResult(BaseModel):
    """Result wrapper for medication lookup."""

    success: bool
    medication: Optional[MedicationInfo] = None
    error_code: Optional[ToolErrorCode] = None
    error_message: Optional[str] = None
    query: Optional[str] = None
    suggestions: Optional[list[str]] = None


# --- Inventory Schemas ---


class InventoryInfo(BaseModel):
    """Inventory information for a medication at a store."""

    med_id: int
    store_id: int
    medication_name_en: str
    medication_name_he: str
    in_stock: bool
    qty: Optional[int] = None
    restock_eta: Optional[str] = None


class InventoryResult(BaseModel):
    """Result wrapper for inventory check."""

    success: bool
    inventory: Optional[InventoryInfo] = None
    error_code: Optional[ToolErrorCode] = None
    error_message: Optional[str] = None


# --- Prescription Schemas ---


class PrescriptionInfo(BaseModel):
    """Information about a single prescription."""

    presc_id: int
    med_id: int
    medication_name_en: str
    medication_name_he: str
    refills_left: int
    status: PrescriptionStatus
    can_refill: bool


class PrescriptionListResult(BaseModel):
    """Result for LIST action."""

    success: bool
    user_name: Optional[str] = None
    prescriptions: Optional[list[PrescriptionInfo]] = None
    error_code: Optional[ToolErrorCode] = None
    error_message: Optional[str] = None


class RefillStatusResult(BaseModel):
    """Result for REFILL_STATUS action."""

    success: bool
    prescription: Optional[PrescriptionInfo] = None
    refill_eligible: Optional[bool] = None
    reason: Optional[str] = None
    error_code: Optional[ToolErrorCode] = None
    error_message: Optional[str] = None
