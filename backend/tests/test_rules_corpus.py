def test_load_mtsp_limits_returns_all_household_sizes():
    from rules_corpus import load_mtsp_limits

    corpus = load_mtsp_limits()
    assert corpus["area_name"] == "Boston-Cambridge-Quincy, MA-NH HUD Metro FMR Area"
    assert set(corpus["limits"].keys()) == set(range(1, 9))
    assert corpus["limits"][4]["60"] == 102840
    assert corpus["limits"][4]["50"] == 85700
    assert corpus["effective_date"]
    assert corpus["source_url"].startswith("https://www.huduser.gov")
