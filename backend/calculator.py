from rules_corpus import load_mtsp_limits

FREQUENCY = {"weekly": 52, "biweekly": 26, "semimonthly": 24, "monthly": 12, "annual": 1}


def parse_confirmed_amount(value: str) -> float:
    """Parse a renter-confirmed dollar amount, tolerating the currency formatting
    ("$2,166.00") that vision-extracted fields (backend/extraction.py's image path)
    return, unlike plain-text extraction which yields bare numbers."""
    return float(value.replace("$", "").replace(",", "").strip())


def annualize(amount: float, frequency: str) -> float:
    if frequency not in FREQUENCY:
        raise ValueError(f"Unsupported frequency: {frequency}")
    if amount < 0:
        raise ValueError("Amount must be non-negative")
    return round(float(amount) * FREQUENCY[frequency], 2)


def compare_to_threshold(annual_income: float, threshold: float) -> str:
    if annual_income < 0 or threshold < 0:
        raise ValueError("Values must be non-negative")
    return "below_or_equal" if annual_income <= threshold else "above"


def calculate_income_vs_threshold(
    confirmed_annual_income: float,
    household_size: int,
    ami_tier: str = "60",
) -> dict:
    if household_size < 1 or household_size > 8:
        raise ValueError("household_size must be between 1 and 8")
    if ami_tier not in ("50", "60"):
        raise ValueError("ami_tier must be '50' or '60'")

    corpus = load_mtsp_limits()
    threshold = corpus["limits"][household_size][ami_tier]

    return {
        "confirmed_value": confirmed_annual_income,
        "threshold": threshold,
        "formula": f"{ami_tier}% AMI limit for household size {household_size} in {corpus['area_name']}",
        "gap": confirmed_annual_income - threshold,
        "source_citation": corpus["area_name"],
        "source_url": corpus["source_url"],
        "effective_date": corpus["effective_date"],
    }
