# Data Quality Report

## Executive Summary

The supplied dataset covers 2024-01-01 00:02:27 to 2026-09-06 21:23:52 across 17 tables. The pipeline preserves raw files, audits keys/FKs/timestamps/categories, and creates clean/golden outputs.

Major recovery impact: raw successful payments totaled INR 1,341,485,926; validated successful payments totaled INR 1,149,682,230; duplicate/payment-status treatment reduced recovery by INR 191,803,696.

## Major Findings

| Issue | Detection | Treatment | Affected Records | Business Impact |
|---|---|---|---:|---|
| agents duplicates | duplicate audit | classify, do not blanket drop | 30000 duplicate-ID rows | affects source trust |
| borrowers duplicates | duplicate audit | classify, do not blanket drop | 28151 duplicate-ID rows | affects source trust |
| calls duplicates | duplicate audit | classify, do not blanket drop | 2700 duplicate-ID rows | affects source trust |
| whatsapp_events duplicates | duplicate audit | classify, do not blanket drop | 1200 duplicate-ID rows | affects source trust |
| payments duplicates | duplicate audit | classify, do not blanket drop | 1000 duplicate-ID rows | affects source trust |
| campaigns duplicates | duplicate audit | classify, do not blanket drop | 0 duplicate-ID rows | affects source trust |
| daily_targeting duplicates | duplicate audit | classify, do not blanket drop | 0 duplicate-ID rows | affects source trust |
| agent_sessions duplicates | duplicate audit | classify, do not blanket drop | 0 duplicate-ID rows | affects source trust |
| borrowers primary key | key audit | keep raw, resolve in clean/golden | 19585 duplicate keys | affects joins |
| agents primary key | key audit | keep raw, resolve in clean/golden | 29000 duplicate keys | affects joins |
| calls primary key | key audit | keep raw, resolve in clean/golden | 1350 duplicate keys | affects joins |
| whatsapp_events primary key | key audit | keep raw, resolve in clean/golden | 600 duplicate keys | affects joins |
| payments primary key | key audit | keep raw, resolve in clean/golden | 500 duplicate keys | affects joins |

## Foreign Keys

Unmatched FK rows are written to `data/processed/audit_outputs/fk_integrity.csv`; they are not silently deleted because they may represent late-arriving or historical source mismatches.

## Cleaning Impact

See `data/processed/audit_outputs/cleaning_impact.csv`.

## Residual Risks

Client and language dimensions are unavailable in supplied data. Actual cost facts are unavailable, so cost per recovered rupee and investment ROI are modeled assumptions rather than observed financial accounting.
