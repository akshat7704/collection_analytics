# Collections Performance Forensics & Recovery Analytics

## Business Problem

This project rebuilds collections performance from raw operational data, challenges a reported 11% month-on-month recovery improvement, identifies drivers, and evaluates where INR 10 Cr should be invested.

## Approach

Raw data -> audit/forensics -> source-of-truth decisions -> clean/golden data -> metric definitions -> monthly reconstruction -> claim validation -> drivers/statistics -> counterfactual -> investment case -> dashboard/memo/architecture.

## Stack

Python, pandas, DuckDB-oriented SQL, matplotlib, pytest, and Power BI-ready CSV outputs.

## Key Findings

- Observation period: 2024-01-01 00:02:27 to 2026-09-06 21:23:52.
- Raw successful recovery: INR 1,341,485,926.
- Validated successful recovery: INR 1,149,682,230.
- Latest independent recovery rate: 0.36%.
- Latest reported-proxy MoM change: -74.49%.
- Latest independent MoM recovery-rate change: -74.67%.
- Recommendation: invest INR 10 Cr in **WhatsApp/digital engagement**, subject to pilot validation.

## Repository Structure

- `data/raw`: unchanged supplied CSVs
- `data/processed/audit_outputs`: inventory, DQ, forensics, cleaning impact
- `data/golden`: dimensions, facts, and analytical account-month table
- `sql`: reproducible SQL definitions and metric templates
- `notebooks`: assignment narrative notebooks
- `outputs/tables`: final analytical tables
- `outputs/charts`: dashboard/report charts
- `dashboard`: executive dashboard HTML/spec and screenshot
- `reports`: memo, DQ report, assumptions, decisions, source of truth
- `architecture`: draw.io and PNG architecture
- `tests`: data quality, metric, attribution, reconciliation tests

## Reproduction

```powershell
cd collections-analytics
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\build_pipeline.py
.\.venv\Scripts\python.exe -m pytest
```

## Limitations

Client, language, and actual cost facts are unavailable in the supplied data. Channel/targeting/campaign effects are observational correlations, not causal proof. A randomized or quasi-experimental design with cost capture is required for a causal investment decision.
