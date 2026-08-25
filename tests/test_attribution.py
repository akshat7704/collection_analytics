import pandas as pd
from src.attribution import attribute_payments


def test_attribute_payments_window():
    payments = pd.DataFrame({"payment_id": ["p1"], "account_id": ["a1"], "amount": [10], "event_at_local": pd.to_datetime(["2026-01-03"]).tz_localize("Asia/Kolkata")})
    touches = pd.DataFrame({"account_id": ["a1"], "touch_at_local": pd.to_datetime(["2026-01-01"]).tz_localize("Asia/Kolkata"), "event_at_local": pd.to_datetime(["2026-01-01"]).tz_localize("Asia/Kolkata"), "channel": ["SMS"], "campaign_id": ["c1"]})
    out = attribute_payments(payments, touches, 3)
    assert out["channel"].iloc[0] == "SMS"
