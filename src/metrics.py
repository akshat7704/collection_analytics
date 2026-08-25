from __future__ import annotations

import numpy as np
import pandas as pd


CONTACT_STATUSES = {"ANSWERED", "CONNECTED", "CONTACTED"}
RPC_CODES = {"RPC", "PTP", "PROMISE_TO_PAY", "RIGHT_PARTY_CONTACT", "PAID", "CALLBACK"}
PTP_CODES = {"PTP", "PROMISE_TO_PAY"}


def safe_divide(num, den):
    return np.where(pd.Series(den).astype(float) == 0, np.nan, pd.Series(num).astype(float) / pd.Series(den).astype(float))


def monthly_scorecard(
    accounts: pd.DataFrame,
    targeting: pd.DataFrame,
    calls: pd.DataFrame,
    dispositions: pd.DataFrame,
    ptp: pd.DataFrame,
    payments: pd.DataFrame,
    sessions: pd.DataFrame,
) -> pd.DataFrame:
    months = sorted(
        set(targeting["month"].dropna())
        | set(calls["month"].dropna())
        | set(payments["month"].dropna())
        | set(ptp["month"].dropna())
    )
    records = []
    total_outstanding = pd.to_numeric(accounts["outstanding_amount"], errors="coerce").sum()
    for month in months:
        targeted = targeting[targeting["month"] == month]
        month_calls = calls[calls["month"] == month]
        month_disp = dispositions[dispositions["month"] == month]
        month_ptp = ptp[ptp["month"] == month]
        month_pay = payments[payments["month"] == month]
        month_sessions = sessions[sessions["month"] == month] if "month" in sessions.columns else sessions.iloc[0:0]

        eligible_accounts = accounts["account_id"].nunique()
        targeted_accounts = targeted["account_id"].nunique()
        attempted_accounts = month_calls["account_id"].nunique()
        contacted_accounts = month_calls[month_calls["call_status"].isin(CONTACT_STATUSES)]["account_id"].nunique()
        rpc_accounts = month_disp[month_disp["is_rpc"]]["account_id"].nunique() if "is_rpc" in month_disp else 0
        ptp_accounts = month_ptp["account_id"].nunique()
        kept_ptp_accounts = month_ptp[month_ptp["is_kept"]]["account_id"].nunique() if "is_kept" in month_ptp else 0
        recovered_amount = pd.to_numeric(month_pay["amount"], errors="coerce").sum()
        session_hours = pd.to_numeric(month_sessions.get("session_hours", pd.Series(dtype=float)), errors="coerce").sum()

        records.append(
            {
                "month": month,
                "eligible_accounts": eligible_accounts,
                "targeted_accounts": targeted_accounts,
                "attempted_accounts": attempted_accounts,
                "contacted_accounts": contacted_accounts,
                "rpc_accounts": rpc_accounts,
                "ptp_accounts": ptp_accounts,
                "ptp_kept_accounts": kept_ptp_accounts,
                "recovered_amount": recovered_amount,
                "total_outstanding_amount": total_outstanding,
                "agent_hours": session_hours,
                "contact_rate": contacted_accounts / attempted_accounts if attempted_accounts else np.nan,
                "rpc_rate": rpc_accounts / contacted_accounts if contacted_accounts else np.nan,
                "ptp_rate": ptp_accounts / rpc_accounts if rpc_accounts else np.nan,
                "ptp_kept_rate": kept_ptp_accounts / ptp_accounts if ptp_accounts else np.nan,
                "recovery_rate": recovered_amount / total_outstanding if total_outstanding else np.nan,
                "recovery_per_account": recovered_amount / eligible_accounts if eligible_accounts else np.nan,
                "recovery_per_agent_hour": recovered_amount / session_hours if session_hours else np.nan,
                "cost_per_recovered_rupee": np.nan,
            }
        )
    scorecard = pd.DataFrame(records).sort_values("month")
    for col in ["recovered_amount", "recovery_rate", "recovery_per_account", "contact_rate", "ptp_kept_rate"]:
        scorecard[f"{col}_mom_abs_change"] = scorecard[col].diff()
        scorecard[f"{col}_mom_pct_change"] = scorecard[col].pct_change()
    return scorecard


def validate_mom_claim(monthly: pd.DataFrame, claim_rate: float = 0.11) -> pd.DataFrame:
    """Compare reported and independent rates only where the prior month is valid."""
    required = ["month", "reported_metric_proxy", "recovery_rate", "eligible_accounts"]
    missing = [column for column in required if column not in monthly.columns]
    if missing:
        raise KeyError(f"Missing claim-validation columns: {missing}")
    claim = monthly[required + ["targeted_accounts"]].copy() if "targeted_accounts" in monthly else monthly[required].copy()
    claim["reported_mom_pct_change"] = claim["reported_metric_proxy"].pct_change()
    claim["independent_mom_pct_change"] = claim["recovery_rate"].pct_change()
    valid = (
        claim["reported_metric_proxy"].shift(1).gt(0)
        & claim["recovery_rate"].shift(1).gt(0)
        & claim["reported_metric_proxy"].replace([np.inf, -np.inf], np.nan).notna()
        & claim["recovery_rate"].replace([np.inf, -np.inf], np.nan).notna()
    )
    claim.loc[~valid, ["reported_mom_pct_change", "independent_mom_pct_change"]] = np.nan
    claim["absolute_gap"] = claim["reported_mom_pct_change"] - claim["independent_mom_pct_change"]
    claim["relative_gap"] = claim["absolute_gap"] / claim["independent_mom_pct_change"].replace({0: np.nan})
    claim["population_change"] = claim["eligible_accounts"].pct_change()
    claim["comparison_status"] = np.where(valid, "valid_month_on_month_comparison", "not_evaluable_no_valid_prior_month")
    claim["conclusion"] = np.select(
        [~valid, claim["independent_mom_pct_change"].sub(claim_rate).abs().le(0.01)],
        ["not evaluable because the prior month has no positive comparable recovery", "partially supported by independent metric for this month"],
        default="not supported as a general claim by the independent metric/proxy alignment",
    )
    return claim


def metric_dictionary() -> pd.DataFrame:
    rows = [
        ("contact_rate", "Ability to reach borrowers", "account-month", "contacted accounts", "attempted accounts", "accounts with at least one call attempt", "invalid/unmatched calls", "same month", "fact_calls", "Answered call is used as contact proxy."),
        ("rpc_rate", "Right-party-contact conversion", "account-month", "accounts with RPC disposition", "contacted accounts", "contacted accounts", "unmapped dispositions", "same month", "fact_call_dispositions + fact_calls", "Disposition semantics depend on canonical mapping."),
        ("ptp_rate", "Promise generation after RPC", "account-month", "accounts with PTP", "RPC accounts", "RPC accounts", "invalid PTPs", "same month", "fact_ptp + fact_call_dispositions", "PTPs from non-call sources are retained but metric denominator is RPC."),
        ("ptp_kept_rate", "Promise quality", "account-month", "kept PTP accounts", "PTP accounts", "PTP accounts", "cancelled/invalid PTPs", "due date + attribution window", "fact_ptp + fact_payments", "Kept status and payment matching are observational."),
        ("recovery_rate", "Cash recovery against portfolio", "month", "validated successful recovered amount", "outstanding amount", "all supplied accounts", "duplicate/failed/reversed payments", "payment month", "fact_payments + dim_account", "Outstanding is static in supplied data."),
        ("recovery_per_account", "Operational cash yield", "month", "validated successful recovered amount", "eligible accounts", "all supplied accounts", "duplicate/failed/reversed payments", "payment month", "fact_payments", "Uses full supplied population."),
        ("recovery_per_agent_hour", "Agent productivity", "month", "validated successful recovered amount", "logged agent hours", "sessions with valid login/logout", "invalid sessions", "payment month", "fact_payments + agent_sessions", "Payment attribution to hours is aggregate, not causal."),
        ("cost_per_recovered_rupee", "Cost efficiency", "month", "modeled costs", "validated recovery", "options with explicit assumptions", "unavailable actual cost records", "scenario", "investment model", "Actual operating costs unavailable in supplied data."),
        ("channel_conversion", "Channel response", "channel-month", "accounts with payment after channel touch", "accounts touched by channel", "channel-touched accounts", "unattributed/organic payments", "configurable 3/7/14/30 days", "fact_digital/calls/field + fact_payments", "Association is not causal."),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "metric",
            "purpose",
            "grain",
            "numerator",
            "denominator",
            "eligible_population",
            "exclusions",
            "attribution_window",
            "source_tables",
            "limitations",
        ],
    )
