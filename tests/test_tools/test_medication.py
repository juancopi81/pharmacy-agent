"""Tests for get_medication_by_name tool."""

import pytest

from apps.api.tools import get_medication_by_name
from apps.api.tools.schemas import ToolErrorCode


@pytest.mark.asyncio
async def test_medication_exact_match_english(test_db):
    """Test exact match for English medication name."""
    result = await get_medication_by_name.ainvoke({"medication_name": "Ibuprofen"})

    assert result["success"] is True
    assert result["medication"]["med_id"] == 1
    assert result["medication"]["name_en"] == "Ibuprofen"
    assert result["medication"]["name_he"] == "איבופרופן"
    assert result["medication"]["rx_required"] is False


@pytest.mark.asyncio
async def test_medication_exact_match_hebrew(test_db):
    """Test exact match for Hebrew medication name."""
    result = await get_medication_by_name.ainvoke({"medication_name": "איבופרופן"})

    assert result["success"] is True
    assert result["medication"]["med_id"] == 1
    assert result["medication"]["name_en"] == "Ibuprofen"


@pytest.mark.asyncio
async def test_medication_case_insensitive(test_db):
    """Test case-insensitive matching for English names."""
    result = await get_medication_by_name.ainvoke({"medication_name": "IBUPROFEN"})

    assert result["success"] is True
    assert result["medication"]["med_id"] == 1


@pytest.mark.asyncio
async def test_medication_not_found(test_db):
    """Test NOT_FOUND error for non-existent medication."""
    result = await get_medication_by_name.ainvoke(
        {"medication_name": "NonExistentMed"}
    )

    assert result["success"] is False
    assert result["error_code"] == ToolErrorCode.NOT_FOUND.value
    assert "query" in result


@pytest.mark.asyncio
async def test_medication_empty_name(test_db):
    """Test error for empty medication name."""
    result = await get_medication_by_name.ainvoke({"medication_name": ""})

    assert result["success"] is False
    assert result["error_code"] == ToolErrorCode.NOT_FOUND.value


@pytest.mark.asyncio
async def test_medication_partial_match(test_db):
    """Test partial matching for medication names."""
    result = await get_medication_by_name.ainvoke({"medication_name": "Ibu"})

    # Should find Ibuprofen
    assert result["success"] is True
    assert result["medication"]["name_en"] == "Ibuprofen"


@pytest.mark.asyncio
async def test_medication_rx_required(test_db):
    """Test medication with prescription requirement."""
    result = await get_medication_by_name.ainvoke({"medication_name": "Amoxicillin"})

    assert result["success"] is True
    assert result["medication"]["rx_required"] is True
