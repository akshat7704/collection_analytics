-- Golden account-month grain used for independent recovery metrics.
CREATE OR REPLACE TABLE fact_collection_episode AS
WITH months AS (
    SELECT DISTINCT DATE_TRUNC('month', TRY_CAST(event_at AS TIMESTAMP)) AS month
    FROM clean_payments
    WHERE TRY_CAST(event_at AS TIMESTAMP) IS NOT NULL
), recovery AS (
    SELECT account_id, DATE_TRUNC('month', TRY_CAST(event_at AS TIMESTAMP)) AS month,
           SUM(amount_num) AS recovered_amount
    FROM clean_payments
    GROUP BY account_id, month
)
SELECT
    a.account_id,
    m.month,
    a.dpd,
    a.risk_segment,
    a.loan_type,
    a.outstanding_amount,
    COALESCE(r.recovered_amount, 0) AS recovered_amount,
    COALESCE(r.recovered_amount, 0) / NULLIF(a.outstanding_amount, 0) AS recovery_rate
FROM dim_account a
CROSS JOIN months m
LEFT JOIN recovery r USING (account_id, month);
