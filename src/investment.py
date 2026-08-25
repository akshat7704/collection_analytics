from __future__ import annotations

import numpy as np
import pandas as pd


INVESTMENT_AMOUNT = 100_000_000


def build_investment_scorecard(channel_perf: pd.DataFrame, vendor_perf: pd.DataFrame, targeting_lift: pd.DataFrame) -> pd.DataFrame:
    """Create assumption-labeled scenarios because actual vendor/unit costs are absent."""
    base_recovery = max(channel_perf["recovered_amount"].sum(), 1.0)
    digital = channel_perf[channel_perf["channel"].isin(["WHATSAPP", "SMS"])]
    best_digital_rate = digital["conversion_rate"].max() if not digital.empty else np.nan
    overall_rate = channel_perf["conversion_rate"].mean()
    vendor_spread = vendor_perf["recovery_per_attempt"].max() - vendor_perf["recovery_per_attempt"].min() if len(vendor_perf) else np.nan
    targeting_signal = targeting_lift["recovery_rate_gap"].iloc[0] if len(targeting_lift) else np.nan

    assumptions = [
        ("Better telephony infrastructure", "Modeled assumption: reduce failed/no-answer leakage by 3%-6%; actual telephony costs unavailable.", 0.03, 0.06, "MEDIUM" if pd.notna(vendor_spread) and vendor_spread > 0 else "LOW"),
        ("More collection agents", "Modeled assumption: add capacity with diminishing returns of 2%-5%; salary/productivity costs unavailable.", 0.02, 0.05, "LOW"),
        ("AI voice automation", "Modeled assumption: automate low-risk reminders for 2%-7%; implementation/vendor costs unavailable.", 0.02, 0.07, "LOW"),
        ("Better borrower targeting", "Modeled from observed targeted-vs-untargeted recovery gap; causal proof unavailable.", max(0.01, min(0.04, abs(targeting_signal) if pd.notna(targeting_signal) else 0.02)), max(0.03, min(0.09, abs(targeting_signal) * 1.5 if pd.notna(targeting_signal) else 0.05)), "MEDIUM"),
        ("WhatsApp/digital engagement", "Modeled from observed digital conversion benchmark; channel costs unavailable.", 0.02 if pd.isna(best_digital_rate) or best_digital_rate <= overall_rate else 0.04, 0.06 if pd.isna(best_digital_rate) or best_digital_rate <= overall_rate else 0.10, "MEDIUM"),
        ("Field operations", "Modeled assumption: recover hard buckets at 2%-6%; travel/vendor costs unavailable.", 0.02, 0.06, "LOW"),
    ]
    rows = []
    for option, evidence, downside_uplift, expected_uplift, confidence in assumptions:
        incremental_recovery = base_recovery * expected_uplift
        downside_recovery = base_recovery * downside_uplift
        rows.append(
            {
                "option": option,
                "observed_evidence": evidence,
                "affected_population": "Supplied overdue collections portfolio; exact deployable population unavailable in source data.",
                "baseline_recovery": base_recovery,
                "expected_uplift": expected_uplift,
                "incremental_recovery": incremental_recovery,
                "modeled_cost": INVESTMENT_AMOUNT,
                "roi": incremental_recovery / INVESTMENT_AMOUNT,
                "break_even_recovery_required": INVESTMENT_AMOUNT,
                "confidence": confidence,
                "downside_incremental_recovery": downside_recovery,
                "downside_roi": downside_recovery / INVESTMENT_AMOUNT,
            }
        )
    df = pd.DataFrame(rows)
    confidence_rank = {"MEDIUM": 2, "LOW": 1}
    df["recommendation_score"] = df["roi"] * df["confidence"].map(confidence_rank)
    return df.sort_values(["recommendation_score", "roi"], ascending=False)
