-- Validated cash recovery: retain successful events and one row per payment reference.
CREATE OR REPLACE TABLE clean_payments AS
WITH ranked AS (
    SELECT
        *,
        TRY_CAST(amount AS DOUBLE) AS amount_num,
        ROW_NUMBER() OVER (
            PARTITION BY NULLIF(TRIM(payment_reference), '')
            ORDER BY event_at, payment_id
        ) AS reference_rank
    FROM stg_payments
    WHERE UPPER(TRIM(payment_status)) = 'SUCCESS'
)
SELECT * EXCLUDE (reference_rank)
FROM ranked
WHERE reference_rank = 1 OR NULLIF(TRIM(payment_reference), '') IS NULL;

-- Reconciliation should equal the clean source used by Python and dashboards.
SELECT
    COUNT(*) AS validated_payment_rows,
    SUM(amount_num) AS validated_successful_amount
FROM clean_payments;
