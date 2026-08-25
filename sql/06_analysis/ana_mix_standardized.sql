-- Fixed-mix diagnostic: hold the portfolio outstanding mix constant by risk segment.
WITH segment_month AS (
    SELECT
        month,
        risk_segment,
        SUM(recovered_amount) / NULLIF(SUM(outstanding_amount), 0) AS segment_rate
    FROM fact_collection_episode
    GROUP BY month, risk_segment
), fixed_weights AS (
    SELECT risk_segment,
           SUM(outstanding_amount) / SUM(SUM(outstanding_amount)) OVER () AS weight
    FROM dim_account
    GROUP BY risk_segment
)
SELECT
    s.month,
    SUM(s.segment_rate * w.weight) AS standardized_recovery_rate
FROM segment_month s
JOIN fixed_weights w USING (risk_segment)
GROUP BY s.month
ORDER BY s.month;
