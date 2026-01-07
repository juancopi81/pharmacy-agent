"""Tests for prescription_management tool."""

import pytest

from apps.api.tools import prescription_management
from apps.api.tools.schemas import ToolErrorCode


@pytest.mark.asyncio
async def test_prescription_list_by_email(test_db):
    """Test listing prescriptions by email."""
    result = await prescription_management.ainvoke({
        "user_identifier": "david.cohen@example.com",
        "action": "LIST",
    })

    assert result["success"] is True
    assert result["user_name"] == "David Cohen"
    assert len(result["prescriptions"]) == 2


@pytest.mark.asyncio
async def test_prescription_list_by_phone(test_db):
    """Test listing prescriptions by phone number."""
    result = await prescription_management.ainvoke({
        "user_identifier": "050-1234567",
        "action": "LIST",
    })

    assert result["success"] is True
    assert result["user_name"] == "David Cohen"
    assert len(result["prescriptions"]) == 2


@pytest.mark.asyncio
async def test_prescription_user_not_found(test_db):
    """Test UNAUTHORIZED error for non-existent user."""
    result = await prescription_management.ainvoke({
        "user_identifier": "unknown@example.com",
        "action": "LIST",
    })

    assert result["success"] is False
    assert result["error_code"] == ToolErrorCode.UNAUTHORIZED.value


@pytest.mark.asyncio
async def test_prescription_refill_eligible(test_db):
    """Test REFILL_STATUS for eligible prescription."""
    result = await prescription_management.ainvoke({
        "user_identifier": "david.cohen@example.com",
        "action": "REFILL_STATUS",
        "prescription_id": 1,
    })

    assert result["success"] is True
    assert result["refill_eligible"] is True
    assert result["prescription"]["refills_left"] == 2
    assert "available" in result["reason"].lower()


@pytest.mark.asyncio
async def test_prescription_refill_not_eligible_completed(test_db):
    """Test REFILL_STATUS for completed prescription."""
    result = await prescription_management.ainvoke({
        "user_identifier": "david.cohen@example.com",
        "action": "REFILL_STATUS",
        "prescription_id": 2,
    })

    assert result["success"] is True
    assert result["refill_eligible"] is False
    assert "completed" in result["reason"].lower()


@pytest.mark.asyncio
async def test_prescription_refill_not_eligible_expired(test_db):
    """Test REFILL_STATUS for expired prescription."""
    result = await prescription_management.ainvoke({
        "user_identifier": "sarah.levi@example.com",
        "action": "REFILL_STATUS",
        "prescription_id": 5,
    })

    assert result["success"] is True
    assert result["refill_eligible"] is False
    assert "expired" in result["reason"].lower()


@pytest.mark.asyncio
async def test_prescription_refill_wrong_user(test_db):
    """Test REFILL_STATUS when prescription belongs to different user."""
    # Prescription 1 belongs to David, not Sarah
    result = await prescription_management.ainvoke({
        "user_identifier": "sarah.levi@example.com",
        "action": "REFILL_STATUS",
        "prescription_id": 1,
    })

    assert result["success"] is False
    assert result["error_code"] == ToolErrorCode.NOT_FOUND.value


@pytest.mark.asyncio
async def test_prescription_refill_missing_id(test_db):
    """Test REFILL_STATUS without prescription_id."""
    result = await prescription_management.ainvoke({
        "user_identifier": "david.cohen@example.com",
        "action": "REFILL_STATUS",
    })

    assert result["success"] is False
    assert result["error_code"] == ToolErrorCode.NOT_FOUND.value


@pytest.mark.asyncio
async def test_prescription_invalid_action(test_db):
    """Test error for invalid action."""
    result = await prescription_management.ainvoke({
        "user_identifier": "david.cohen@example.com",
        "action": "INVALID_ACTION",
    })

    assert result["success"] is False
    assert result["error_code"] == ToolErrorCode.INVALID_STATE.value


@pytest.mark.asyncio
async def test_prescription_can_refill_field(test_db):
    """Test can_refill computed field in prescription info."""
    result = await prescription_management.ainvoke({
        "user_identifier": "david.cohen@example.com",
        "action": "LIST",
    })

    assert result["success"] is True

    # Find the active prescription with refills
    active_presc = next(
        p for p in result["prescriptions"]
        if p["status"] == "active" and p["refills_left"] > 0
    )
    assert active_presc["can_refill"] is True

    # Find the completed prescription
    completed_presc = next(
        p for p in result["prescriptions"]
        if p["status"] == "completed"
    )
    assert completed_presc["can_refill"] is False
