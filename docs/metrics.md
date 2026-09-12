# Metrics

| Metric | Definition |
|--------|------------|
| DiscoveryEfficiency | confirmed novel findings / experiments executed |
| ExplorationCoverage | unique behavioral regions / estimated reachable regions |
| FalsePositiveRate | findings marked potentially_vulnerable that fail verification / all such candidates |
| ReproRate | independently reproduced findings / candidates sent to verifier |
| CorpusEscapeRate | confirmed findings whose ground-truth ID is outside corpus ∩ ground-truth / confirmed |
| tests_per_discovery | experiments / max(1, confirmed novel findings) |
| AnomalyRate | anomalous observations / experiments |
| ConfirmedCount | count of status=`confirmed` |

All metrics are computed from SQLite experiment/finding stores after runs.
