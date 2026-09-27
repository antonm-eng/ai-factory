# Model Card: prepaid churn <version>

| Field | Value |
|---|---|
| Model | prepaid churn `<version>` (SageMaker Model Registry group `prepaid-churn`) |
| Owner | Data Science (Elvin R.) |
| Status | `<registry approval status>` |
| Review date | `<date>` |

## Intended use
Rank prepaid subscribers by 30-day churn risk for CVM retention campaigns. Not for credit, pricing or any individual-level decision outside CVM.

## Population and data
Active prepaid subscribers. Features from `ai_factory.churn_features` (see `docs/data_dictionary.md`), snapshot `<features_run_id>`, contract `recharge_events <version>`.

## Metrics at the operating point (top 10% risk, frozen window 2026-08)
| Metric | This version | Current approved |
|---|---|---|
| Precision | | |
| Recall | | |
| F1 | | |
| AUC | | |

## Known limitations
<from the evaluation and the data checks>

## Lineage
Code version, features run id, training job, evaluation report location.

## To be written by people
- Business justification: _requested from the CVM owner_
- Fairness considerations: _requested from the AI Steward_
