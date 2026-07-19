import pytest


def test_annualize_weekly():
    from calculator import annualize

    assert annualize(1000, "weekly") == 52000


def test_annualize_biweekly():
    from calculator import annualize

    assert annualize(2000, "biweekly") == 52000


def test_compare_to_threshold_boundary():
    from calculator import compare_to_threshold

    assert compare_to_threshold(72000, 72000) == "below_or_equal"


def test_compare_to_threshold_above():
    from calculator import compare_to_threshold

    assert compare_to_threshold(72000.01, 72000) == "above"


def test_annualize_unknown_frequency():
    from calculator import annualize

    with pytest.raises(ValueError):
        annualize(1000, "fortnight-ish")


def test_calculate_income_vs_threshold_uses_real_corpus():
    from calculator import calculate_income_vs_threshold

    result = calculate_income_vs_threshold(confirmed_annual_income=90000, household_size=4, ami_tier="60")
    assert result["threshold"] == 102840
    assert result["confirmed_value"] == 90000
    assert result["gap"] == 90000 - 102840
    assert "effective_date" in result
    assert "source_citation" in result


def test_annualize_matches_hh001_real_data():
    # HH-001 (regular_hourly): hh-001_d03_pay_stub.pdf has PAY FREQUENCY=biweekly,
    # GROSS PAY=$2,166.00. Expected annualized income per
    # data/evaluation/application_checklists.json's expected_annualized_income for HH-001
    # is 56316.0.
    from calculator import annualize

    assert annualize(2166.00, "biweekly") == 56316.0


def test_annualize_matches_hh002_real_data():
    # HH-002 (overtime_variance): hh-002_d03_pay_stub.pdf has PAY FREQUENCY=weekly,
    # GROSS PAY=$960.00 (regular rate, excludes overtime). Expected annualized income per
    # data/evaluation/application_checklists.json's expected_annualized_income for HH-002
    # is 49920.0.
    from calculator import annualize

    assert annualize(960.00, "weekly") == 49920.0


def test_calculate_rejects_invalid_household_size():
    from calculator import calculate_income_vs_threshold

    with pytest.raises(ValueError):
        calculate_income_vs_threshold(confirmed_annual_income=50000, household_size=9, ami_tier="60")
