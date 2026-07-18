import json

import pytest


def test_load_mtsp_limits_returns_all_household_sizes():
    from rules_corpus import load_mtsp_limits

    corpus = load_mtsp_limits()
    assert corpus["area_name"] == "Boston-Cambridge-Quincy, MA-NH HUD Metro FMR Area"
    assert set(corpus["limits"].keys()) == set(range(1, 9))
    assert corpus["limits"][4]["60"] == 102840
    assert corpus["limits"][4]["50"] == 85700
    assert corpus["effective_date"]
    assert corpus["source_url"].startswith("https://www.huduser.gov")


def test_load_mtsp_limits_missing_data_file_raises_clear_error(tmp_path, monkeypatch):
    import rules_corpus

    monkeypatch.setattr(rules_corpus, "DATA_PATH", tmp_path / "does_not_exist.json")

    with pytest.raises(FileNotFoundError, match="does_not_exist.json"):
        rules_corpus.load_mtsp_limits()


def test_load_mtsp_limits_missing_meta_file_raises_clear_error(tmp_path, monkeypatch):
    import rules_corpus

    real_data = tmp_path / "data.json"
    real_data.write_text(rules_corpus.DATA_PATH.read_text())
    monkeypatch.setattr(rules_corpus, "DATA_PATH", real_data)
    monkeypatch.setattr(rules_corpus, "META_PATH", tmp_path / "missing.meta.json")

    with pytest.raises(FileNotFoundError, match="missing.meta.json"):
        rules_corpus.load_mtsp_limits()


def test_load_mtsp_limits_malformed_json_raises_clear_error(tmp_path, monkeypatch):
    import rules_corpus

    bad_data = tmp_path / "bad.json"
    bad_data.write_text("{not valid json")
    monkeypatch.setattr(rules_corpus, "DATA_PATH", bad_data)

    with pytest.raises(json.JSONDecodeError, match="bad.json"):
        rules_corpus.load_mtsp_limits()


def test_load_mtsp_limits_empty_rows_raises_value_error(tmp_path, monkeypatch):
    import rules_corpus

    empty_data = tmp_path / "empty.json"
    empty_data.write_text("[]")
    monkeypatch.setattr(rules_corpus, "DATA_PATH", empty_data)

    with pytest.raises(ValueError, match="no rows"):
        rules_corpus.load_mtsp_limits()
