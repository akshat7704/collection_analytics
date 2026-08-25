from __future__ import annotations

import numpy as np
import pandas as pd


def portfolio_mix(accounts: pd.DataFrame, targeting: pd.DataFrame) -> pd.DataFrame:
    targeted_months = targeting[["account_id", "month"]].drop_duplicates()
    joined = targeted_months.merge(accounts[["account_id", "dpd", "risk_segment", "loan_type", "outstanding_amount", "status"]], on="account_id", how="left")
    if joined.empty:
        return pd.DataFrame()
    joined["dpd_bucket"] = pd.cut(
        pd.to_numeric(joined["dpd"], errors="coerce"),
        bins=[-1, 0, 30, 60, 90, 10_000],
        labels=["current", "1-30", "31-60", "61-90", "90+"],
    )
    return (
        joined.groupby(["month", "dpd_bucket", "risk_segment"], observed=True)
        .agg(accounts=("account_id", "nunique"), outstanding=("outstanding_amount", lambda s: pd.to_numeric(s, errors="coerce").sum()))
        .reset_index()
    )


def targeting_gap(accounts: pd.DataFrame, targeting: pd.DataFrame, payments: pd.DataFrame) -> pd.DataFrame:
    targeted_accounts = set(targeting["account_id"])
    recovery = payments.groupby("account_id")["amount"].apply(lambda s: pd.to_numeric(s, errors="coerce").sum()).rename("recovered")
    base = accounts[["account_id", "outstanding_amount"]].copy()
    base["targeted"] = base["account_id"].isin(targeted_accounts)
    base = base.merge(recovery, on="account_id", how="left").fillna({"recovered": 0})
    base["outstanding_amount"] = pd.to_numeric(base["outstanding_amount"], errors="coerce")
    grouped = base.groupby("targeted").agg(recovered=("recovered", "sum"), outstanding=("outstanding_amount", "sum"), accounts=("account_id", "nunique")).reset_index()
    grouped["recovery_rate"] = grouped["recovered"] / grouped["outstanding"].replace({0: np.nan})
    gap = grouped.loc[grouped["targeted"], "recovery_rate"].mean() - grouped.loc[~grouped["targeted"], "recovery_rate"].mean()
    return pd.DataFrame([{"recovery_rate_gap": gap, "method": "targeted vs non-targeted observational comparison", "causal_status": "Correlation"}])


def vendor_performance(calls: pd.DataFrame, attributed_payments: pd.DataFrame) -> pd.DataFrame:
    attempts = calls.groupby("vendor_id").agg(attempts=("call_id", "nunique"), answered=("call_status", lambda s: s.isin(["ANSWERED", "CONNECTED", "CONTACTED"]).sum())).reset_index()
    pay = attributed_payments.groupby("provider_id").agg(recovered_amount=("amount", lambda s: pd.to_numeric(s, errors="coerce").sum())).reset_index()
    out = attempts.merge(pay, left_on="vendor_id", right_on="provider_id", how="left").drop(columns=["provider_id"], errors="ignore")
    out["recovered_amount"] = out["recovered_amount"].fillna(0.0)
    out["contact_rate"] = out["answered"] / out["attempts"].replace({0: np.nan})
    out["recovery_per_attempt"] = out["recovered_amount"] / out["attempts"].replace({0: np.nan})
    return out.sort_values("recovery_per_attempt", ascending=False)


def mix_standardized_recovery(accounts: pd.DataFrame, payments: pd.DataFrame, group_col: str = "risk_segment") -> pd.DataFrame:
    """Compare monthly recovery at a fixed portfolio mix, avoiding aggregate mix drift."""
    base = accounts[["account_id", "outstanding_amount", group_col]].copy()
    base["outstanding_amount"] = pd.to_numeric(base["outstanding_amount"], errors="coerce")
    pay = payments[["account_id", "amount", "month"]].copy()
    pay["amount"] = pd.to_numeric(pay["amount"], errors="coerce").fillna(0)
    account_month = pay.groupby(["month", "account_id"], as_index=False)["amount"].sum()
    account_month = base.merge(account_month, on="account_id", how="left").fillna({"amount": 0})
    account_month["rate"] = account_month["amount"] / account_month["outstanding_amount"].replace({0: np.nan})
    weights = base.groupby(group_col)["outstanding_amount"].sum()
    weights = weights / weights.sum()
    rows = []
    for month, current in account_month.groupby("month"):
        segment = current.groupby(group_col).agg(recovered=("amount", "sum"), outstanding=("outstanding_amount", "sum"))
        segment["segment_rate"] = segment["recovered"] / segment["outstanding"].replace({0: np.nan})
        rows.append({"month": month, "standardized_recovery_rate": (segment["segment_rate"] * weights).sum(), "standardization_group": group_col})
    return pd.DataFrame(rows).sort_values("month")


def cohort_recovery(accounts: pd.DataFrame, payments: pd.DataFrame) -> pd.DataFrame:
    """Produce transparent account-opening cohorts and cumulative recovery outcomes."""
    base = accounts[["account_id", "opened_at", "outstanding_amount"]].copy()
    base["cohort_month"] = pd.to_datetime(base["opened_at"], errors="coerce").dt.to_period("M").astype(str)
    base["outstanding_amount"] = pd.to_numeric(base["outstanding_amount"], errors="coerce")
    recovered = payments.groupby("account_id")["amount"].sum().rename("recovered_amount")
    out = base.merge(recovered, on="account_id", how="left").fillna({"recovered_amount": 0})
    result = out.groupby("cohort_month", dropna=False).agg(accounts=("account_id", "nunique"), outstanding=("outstanding_amount", "sum"), recovered=("recovered_amount", "sum")).reset_index()
    result["recovery_rate"] = result["recovered"] / result["outstanding"].replace({0: np.nan})
    return result.sort_values("cohort_month")
