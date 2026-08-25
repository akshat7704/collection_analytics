-- Golden account dimension. One row per account, with supplied portfolio attributes.
CREATE OR REPLACE TABLE dim_account AS
SELECT
    account_id,
    borrower_id,
    loan_type,
    TRY_CAST(principal_amount AS DOUBLE) AS principal_amount,
    TRY_CAST(outstanding_amount AS DOUBLE) AS outstanding_amount,
    TRY_CAST(dpd AS INTEGER) AS dpd,
    risk_segment,
    status,
    opened_at,
    timezone,
    schema_version
FROM stg_accounts
QUALIFY ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY opened_at DESC NULLS LAST) = 1;
