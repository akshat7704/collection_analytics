-- Duplicate payment checks used by the Python pipeline.
SELECT
  COUNT(*) AS raw_rows,
  COUNT(*) - COUNT(DISTINCT payment_id) AS duplicate_payment_id_rows,
  COUNT(*) - COUNT(DISTINCT payment_reference) AS duplicate_reference_rows,
  SUM(CASE WHEN payment_status = 'SUCCESS' THEN CAST(amount AS DOUBLE) ELSE 0 END) AS raw_success_amount
FROM stg_payments;
