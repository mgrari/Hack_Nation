from rules_corpus import load_mtsp_limits


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
