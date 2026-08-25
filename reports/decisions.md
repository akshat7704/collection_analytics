# Decision Log

| Decision | Evidence | Alternatives considered | Why chosen | Impact | Confidence |
|---|---|---|---|---|---|
| Preserve raw files and build processed/golden layers | Assignment requires raw untouched | Edit raw CSVs | Auditability | Reproducible rebuild | HIGH |
| Exclude failed payments from recovery | Payment status field exists | Count all payments | Cash recovery requires success | Recovery lowered vs raw totals | HIGH |
| Deduplicate by exact row, payment ID, then payment reference | Duplicate payment audit | Drop all duplicate-looking events | Business-key suspicious repeats may be legitimate | Quantified overstatement | MEDIUM |
| Use account-month as primary scorecard grain | Monthly claim and portfolio funnel | attempt-month only | Avoid denominator mixing | Executive metrics align | HIGH |
| Treat 11% claim as tested proxy unless official report definition supplied | No external reported metric table | Assume claim true/false | Independent validation requires aligned definition | Conclusion can be partial/not verifiable | HIGH |
| Recommend one investment by evidence-adjusted modeled ROI | Assignment asks exactly one option | Multiple recommendations | Forces executive choice | Costs are assumption-labeled | MEDIUM |
