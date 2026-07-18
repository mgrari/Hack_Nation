import pytest


def test_calculate_income_vs_threshold_uses_real_corpus():
    from calculator import calculate_income_vs_threshold

    result = calculate_income_vs_threshold(confirmed_annual_income=90000, household_size=4, ami_tier="60")
    assert result["threshold"] == 102840
    assert result["confirmed_value"] == 90000
    assert result["gap"] == 90000 - 102840
    assert "effective_date" in result
    assert "source_citation" in result


def test_calculate_rejects_invalid_household_size():
    from calculator import calculate_income_vs_threshold

    with pytest.raises(ValueError):
        calculate_income_vs_threshold(confirmed_annual_income=50000, household_size=9, ami_tier="60")
