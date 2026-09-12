-- Recharge recency features for the prepaid churn model.
SELECT
  msisdn_hash,
  CAST(julianday(:as_of) - julianday(MAX(recharge_ts)) AS INTEGER) AS days_since_last_recharge,
  ROUND(MIN(amount_azn), 2)                                         AS min_recharge_30d,
  ROUND(MAX(amount_azn), 2)                                         AS max_recharge_30d
FROM recharge_events
WHERE recharge_ts >= :window_start
GROUP BY msisdn_hash
