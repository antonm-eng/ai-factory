"""Prepaid churn scoring with the approved model: prepaid-churn v2, a logistic scorecard on the recharge features.

The same coefficients back the Athena view ai_factory.retention_list_fresh, so a list built from
fresh features can be compared with the published one.
"""

import math

MODEL = "prepaid-churn v2"
INTERCEPT = -2.8
COEFFICIENTS = {
    "days_since_last_recharge": 0.11,
    "recharge_cnt_30d": -0.18,
    "avg_recharge_30d": -0.04,
    "digital_share_30d": -0.9,
}
LIST_SHARE = 0.10  # the retention campaign targets the top 10% risk


def churn_score(features: dict) -> float:
    z = INTERCEPT + sum(weight * float(features[name]) for name, weight in COEFFICIENTS.items())
    return 1.0 / (1.0 + math.exp(-z))
