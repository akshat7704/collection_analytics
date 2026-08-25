# Requirements Traceability Matrix

This document maps the assignment questions to the implemented analytical artifacts and confirms what is already covered versus what still requires final verification before sign-off.

## 1. Assignment objective

The assignment asks the analyst to determine whether the business claim is true when the raw data is messy, incomplete, contradictory, and potentially misleading. The repo implements this by preserving raw source files, performing forensic auditing, defining a golden layer, validating the reported claim, analyzing drivers, and modeling a final investment recommendation.

## 2. Requirement-to-artifact mapping

| Requirement | Source of truth | Repo artifact(s) | Current status | Notes |
|---|---|---|---|---|
| Reconstruct actual business performance | Raw collections and payment data | `data/golden/analytical/fct_collection_episode.csv`, `outputs/tables/monthly_scorecard.csv`, `outputs/tables/denominator_funnel.csv` | Implemented | Monthly operational reconstruction is present. |
| Determine when performance changed | Monthly trend reconstruction | `outputs/tables/monthly_scorecard.csv`, `outputs/charts/monthly_recovery.png`, `outputs/charts/reported_vs_independent.png` | Implemented | Latest complete month logic is embedded in the pipeline. |
| Determine what and where changed | Mix, DPD, geography, channel inputs | `outputs/tables/portfolio_mix.csv`, `outputs/tables/dpd_scorecard.csv`, `outputs/tables/geography_scorecard.csv`, `outputs/tables/campaign_scorecard.csv`, `outputs/tables/channel_scorecard.csv` | Implemented | Segment-level scorecards are generated. |
| Test whether the 11% claim is real | Independent recovery metric vs proxy metric | `outputs/tables/claim_validation.csv`, `outputs/tables/monthly_scorecard.csv`, `reports/executive_memo.md` | Implemented | Current output reports the claim as not supported by the independent metric/proxy alignment. |
| Define contact, RPC, PTP, kept PTP, recovery, and rate metrics | Metric logic and dictionary | `src/metrics.py`, `outputs/tables/metric_dictionary.csv`, `dashboard/dashboard_metric_dictionary.csv` | Implemented | Metric definitions are explicit and documented. |
| Analyze driver variables | DPD, channel, agency, campaign, attempts, geography, etc. | `outputs/tables/agent_scorecard.csv`, `outputs/tables/vendor_scorecard.csv`, `outputs/tables/calling_time_scorecard.csv`, `outputs/tables/attempt_frequency_scorecard.csv`, `outputs/tables/risk_scorecard.csv`, `outputs/tables/loan_scorecard.csv` | Implemented | Driver analysis is represented as scorecards. |
| Classify conclusions using Fact / Strong Evidence / Correlation / Hypothesis | Statistical summaries and report text | `outputs/tables/statistical_investigation_summary.csv`, `reports/insight_register.csv`, `reports/executive_memo.md` | Partially implemented | Stronger consistency check is still needed before final sign-off. |
| Recommend one investment option under INR 10 Cr | Investment scoring model | `src/investment.py`, `outputs/tables/investment_option_scorecard.csv`, `outputs/tables/investment_scenarios.csv`, `reports/executive_memo.md` | Implemented | Recommendation is present and scenario-based. |
| Document data-quality assumptions and source-of-truth decisions | Forensic audits | `reports/source_of_truth.md`, `reports/assumptions.md`, `reports/decisions.md`, `reports/data_quality_report.md` | Implemented | This is a key strength of the current repo. |
| Package final deliverables | Dashboard + memo + outputs | `dashboard/executive_dashboard.html`, `reports/executive_memo.md`, `outputs/final_submission/` | Implemented | Final packaging is set up, but final content should be checked for internal consistency. |

## 3. Q1–Q4 coverage check

### Q1 — What happened?

Covered by:
- `outputs/tables/monthly_scorecard.csv`
- `outputs/tables/denominator_funnel.csv`
- `outputs/tables/dpd_scorecard.csv`
- `outputs/tables/portfolio_mix.csv`
- `reports/executive_memo.md`

Status: Implemented and evidence-backed.

### Q2 — Why did it happen?

Covered by:
- `outputs/tables/geography_scorecard.csv`
- `outputs/tables/campaign_scorecard.csv`
- `outputs/tables/agent_scorecard.csv`
- `outputs/tables/vendor_scorecard.csv`
- `outputs/tables/calling_time_scorecard.csv`
- `outputs/tables/attempt_frequency_scorecard.csv`
- `outputs/tables/risk_scorecard.csv`
- `outputs/tables/loan_scorecard.csv`
- `outputs/tables/statistical_investigation_summary.csv`

Status: Implemented, but final wording should explicitly mark every conclusion with the required classification labels.

### Q3 — Is the reported 11% improvement real?

Covered by:
- `src/metrics.py`
- `outputs/tables/monthly_scorecard.csv`
- `outputs/tables/claim_validation.csv`
- `reports/executive_memo.md`

Status: Implemented and likely the strongest part of the project.

### Q4 — Where should INR 10 Cr be invested?

Covered by:
- `src/investment.py`
- `outputs/tables/investment_option_scorecard.csv`
- `outputs/tables/investment_scenarios.csv`
- `reports/executive_memo.md`
- `reports/assumptions.md`

Status: Implemented with scenario-level assumptions; final sign-off should confirm the exact recommendation and uncertainty language match the evidence.

## 4. Remaining sign-off checks before final submission

The following checks should be completed as the final implementation pass:

1. Confirm every conclusion in the memo and dashboard is explicitly labeled Fact / Strong Evidence / Correlation / Hypothesis.
2. Verify the recommendation in the memo matches the ranking produced by the investment scorecard.
3. Confirm the report does not overstate causal claims where the data is observational only.
4. Re-run the full pipeline from raw CSVs to final outputs and ensure no artifact is missing.
5. Validate that the assignment PDF and the repo outputs are consistent with one another.

## 5. Overall assessment

The project is substantially implemented and aligned with the assignment’s core goals. It is close to submission-ready, but final polish should focus on consistency, traceability, and conservative causal language rather than adding new analytical scope.
