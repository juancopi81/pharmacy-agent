"""Tests for check_inventory tool."""

import pytest

from apps.api.tools import check_inventory
from apps.api.tools.schemas import ToolErrorCode


@pytest.mark.asyncio
async def test_inventory_in_stock_by_id(test_db):
    """Test checking inventory for in-stock medication by ID."""
    result = await check_inventory.ainvoke({"medication_id": 1})

    assert result["success"] is True
    assert result["inventory"]["in_stock"] is True
    assert result["inventory"]["qty"] == 150
    assert result["inventory"]["restock_eta"] is None
    assert result["inventory"]["medication_name_en"] == "Ibuprofen"


@pytest.mark.asyncio
async def test_inventory_out_of_stock_by_id(test_db):
    """Test checking inventory for out-of-stock medication by ID."""
    result = await check_inventory.ainvoke({"medication_id": 2})

    assert result["success"] is True
    assert result["inventory"]["in_stock"] is False
    assert result["inventory"]["qty"] is None  # Not shown when out of stock
    assert result["inventory"]["restock_eta"] == "2025-01-15"
    assert result["inventory"]["medication_name_en"] == "Amoxicillin"


@pytest.mark.asyncio
async def test_inventory_by_name(test_db):
    """Test checking inventory by medication name."""
    result = await check_inventory.ainvoke({"medication_name": "Cetirizine"})

    assert result["success"] is True
    assert result["inventory"]["in_stock"] is True
    assert result["inventory"]["qty"] == 200


@pytest.mark.asyncio
async def test_inventory_by_hebrew_name(test_db):
    """Test checking inventory by Hebrew medication name."""
    result = await check_inventory.ainvoke({"medication_name": "צטיריזין"})

    assert result["success"] is True
    assert result["inventory"]["medication_name_en"] == "Cetirizine"


@pytest.mark.asyncio
async def test_inventory_not_found(test_db):
    """Test NOT_FOUND error for non-existent medication."""
    result = await check_inventory.ainvoke({"medication_id": 999})

    assert result["success"] is False
    assert result["error_code"] == ToolErrorCode.NOT_FOUND.value


@pytest.mark.asyncio
async def test_inventory_no_identifier(test_db):
    """Test error when no identifier provided."""
    result = await check_inventory.ainvoke({})

    assert result["success"] is False
    assert result["error_code"] == ToolErrorCode.INVALID_STATE.value


@pytest.mark.asyncio
async def test_inventory_prefer_id_over_name(test_db):
    """Test that medication_id is preferred when both provided."""
    # Provide id=1 (Ibuprofen) but name for Amoxicillin
    result = await check_inventory.ainvoke({
        "medication_id": 1,
        "medication_name": "Amoxicillin"
    })

    # Should use ID and return Ibuprofen
    assert result["success"] is True
    assert result["inventory"]["med_id"] == 1
    assert result["inventory"]["medication_name_en"] == "Ibuprofen"
