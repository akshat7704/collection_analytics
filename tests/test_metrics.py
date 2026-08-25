import numpy as np
from src.metrics import monthly_scorecard


def test_monthly_scorecard_known_outputs():
    import pandas as pd
    accounts = pd.DataFrame({"account_id": ["a1", "a2"], "outstanding_amount": [100, 100]})
    targeting = pd.DataFrame({"account_id": ["a1", "a2"], "month": ["2026-01", "2026-01"]})
    calls = pd.DataFrame({"account_id": ["a1", "a2"], "call_status": ["ANSWERED", "NO_ANSWER"], "month": ["2026-01", "2026-01"]})
    disp = pd.DataFrame({"account_id": ["a1"], "is_rpc": [True], "month": ["2026-01"]})
    ptp = pd.DataFrame({"account_id": ["a1"], "is_kept": [True], "month": ["2026-01"]})
    pay = pd.DataFrame({"account_id": ["a1"], "amount": [20], "month": ["2026-01"]})
    sessions = pd.DataFrame({"session_hours": [2.0], "month": ["2026-01"]})
    out = monthly_scorecard(accounts, targeting, calls, disp, ptp, pay, sessions).iloc[0]
    assert out["contact_rate"] == 0.5
    assert out["rpc_rate"] == 1.0
    assert out["ptp_rate"] == 1.0
    assert out["ptp_kept_rate"] == 1.0
    assert out["recovery_rate"] == 0.1
    assert out["recovery_per_account"] == 10
    assert out["recovery_per_agent_hour"] == 10


def test_claim_validation_marks_zero_baseline_as_not_evaluable():
    from src.metrics import validate_mom_claim
    monthly = pd.DataFrame({
        "month": ["2025-12", "2026-01", "2026-02"],
        "reported_metric_proxy": [0.0, 0.02, 0.01],
        "recovery_rate": [0.0, 0.01, 0.02],
        "eligible_accounts": [10, 10, 10],
        "targeted_accounts": [0, 2, 2],
    })
    out = validate_mom_claim(monthly)
    assert pd.isna(out.loc[1, "independent_mom_pct_change"])
    assert out.loc[1, "comparison_status"] == "not_evaluable_no_valid_prior_month"
