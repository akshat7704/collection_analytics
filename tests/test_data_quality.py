import pandas as pd
from src.data_quality import key_integrity


def test_key_integrity_counts_duplicate_ids():
    frames = {"borrowers": pd.DataFrame({"borrower_id": ["b1", "b1", "b2"]})}
    from src import data_quality
    old = data_quality.PRIMARY_KEYS if hasattr(data_quality, "PRIMARY_KEYS") else None
    out = key_integrity({"borrowers": frames["borrowers"], **{k: pd.DataFrame({v: []}) for k, v in __import__("src.config", fromlist=["PRIMARY_KEYS"]).PRIMARY_KEYS.items() if k != "borrowers"}})
    assert int(out[out["dataset"] == "borrowers"]["duplicate_count"].iloc[0]) == 1
