# Prepaid churn: release acceptance criteria

Agreed by Data Science, MLOps and the AI Steward. A candidate in the SageMaker Model Registry group
`prepaid-churn` is released only if every check below passes. Values are illustrative demo data.

## Performance (frozen evaluation window 2026-08-01 to 2026-08-31, operating point: top 10% risk)

1. Precision at the operating point is **at least 0.20** and **not below the current approved version**.
2. F1 at the operating point is **at least 0.30** and **not below the current approved version**.
3. Segment counts per sales channel are within **±10%** of the current approved version.

## Data and lineage

4. Training features come from a **successful** `churn_features_daily` run (recorded as `features_run_id`).
5. That run finished **no more than 24 hours** before training started.
6. The features were built under the **current** `recharge_events` contract version.
7. No feature has a null rate above **2%** in the training snapshot.

## Evidence and decision

8. The evidence pack contains: the metrics comparison with the current approved version, segment counts,
   the data and lineage checks above (with run ids and code versions), and the projected monthly scoring cost.
9. The decision (Approved or Rejected) is recorded in the Model Registry together with the SHA-256 of the
   evidence pack, and is approved by a named person (AI Steward or MLOps lead).
10. A Model Card draft exists before release. Business justification and fairness considerations are written by people.
