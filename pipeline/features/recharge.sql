-- Recharge behaviour features for the prepaid churn model (published as cvm.recharge_30d_v2).
-- Owner: data-engineering. Consumers: churn v2 / v3 scoring, CVM campaign lists.
SELECT
  msisdn_hash,
  COUNT(*)                                                   AS recharge_cnt_30d,
  ROUND(AVG(amount_azn), 2)                                  AS avg_recharge_30d,
  ROUND(SUM(CASE WHEN channel = 'digital' THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 3)
                                                             AS digital_share_30d,
  COUNT(DISTINCT channel)                                    AS channel_cnt_30d,
  MAX(recharge_ts)                                           AS last_recharge_ts
FROM recharge_events
WHERE recharge_ts >= :window_start
GROUP BY msisdn_hash
