-- Valid month-on-month claim validation. Zero baselines are not valid comparisons.
WITH monthly AS (
    SELECT month,
           SUM(recovered_amount) AS validated_recovery,
           SUM(outstanding_amount) AS outstanding_amount
    FROM fact_collection_episode
    GROUP BY month
), rates AS (
    SELECT *,
           validated_recovery / NULLIF(outstanding_amount, 0) AS independent_recovery_rate,
           LAG(validated_recovery / NULLIF(outstanding_amount, 0)) OVER (ORDER BY month) AS prior_rate
    FROM monthly
)
SELECT month,
       independent_recovery_rate,
       independent_recovery_rate / NULLIF(prior_rate, 0) - 1 AS independent_mom_pct_change,
       CASE WHEN prior_rate > 0 THEN 'valid_month_on_month_comparison'
            ELSE 'not_evaluable_no_valid_prior_month' END AS comparison_status
FROM rates
ORDER BY month;
