import pandas as pd
from src.data_quality import payment_duplicate_forensics


def test_payment_reconciliation_duplicate_reference():
    df = pd.DataFrame(
        [
            {"payment_id": "p1", "payment_reference": "r1", "account_id": "a1", "event_at": "2026-01-01", "amount": "100", "payment_status": "SUCCESS", "payment_method": "UPI", "provider_id": "v1"},
            {"payment_id": "p2", "payment_reference": "r1", "account_id": "a1", "event_at": "2026-01-01", "amount": "100", "payment_status": "SUCCESS", "payment_method": "UPI", "provider_id": "v1"},
            {"payment_id": "p3", "payment_reference": "r2", "account_id": "a1", "event_at": "2026-01-02", "amount": "50", "payment_status": "FAILED", "payment_method": "UPI", "provider_id": "v1"},
        ]
    )
    summary, _, clean = payment_duplicate_forensics(df)
    assert summary["raw_successful_payment_amount"].iloc[0] == 200
    assert summary["validated_successful_payment_amount"].iloc[0] == 100
    assert len(clean) == 1
