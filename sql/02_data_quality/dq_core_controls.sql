-- Core publication controls. Run after staging and before clean/golden publication.
SELECT 'accounts_primary_key' AS check_name,
       COUNT(*) - COUNT(DISTINCT account_id) AS failure_count
FROM stg_accounts
UNION ALL
SELECT 'payments_duplicate_references',
       COUNT(*) - COUNT(DISTINCT NULLIF(TRIM(payment_reference), ''))
FROM stg_payments
WHERE NULLIF(TRIM(payment_reference), '') IS NOT NULL
UNION ALL
SELECT 'payments_invalid_amount',
       COUNT(*)
FROM stg_payments
WHERE TRY_CAST(amount AS DOUBLE) IS NULL
UNION ALL
SELECT 'payments_missing_account',
       COUNT(*)
FROM stg_payments p
LEFT JOIN stg_accounts a USING (account_id)
WHERE a.account_id IS NULL;
