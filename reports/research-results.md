# AIVD Research Results (Actual Runs)

## Protocol

Six explorers × 80 experiments on `mock://default`, seed=42. Ground truth used only for offline metrics.

## Results

Comparison seed=42, budget_per_method=80.

| Method | Experiments | Confirmed | DiscoveryEfficiency | CorpusEscapeRate | GT hits |
|--------|-------------|-----------|---------------------|------------------|---------|
| random | 80 | 50 | 0.0625 | 0.6000 | `{'HV-NOVEL-ENCODING': 8, 'HV-CORPUS-ROLE': 14, 'HV-NOVEL-DELIMITER': 8, 'HV-CORPUS-INJECT': 8, 'HV-NOVEL-INDIRECT': 12}` |
| corpus | 80 | 54 | 0.0250 | 0.0000 | `{'HV-CORPUS-INJECT': 28, 'HV-CORPUS-ROLE': 26}` |
| novelty | 80 | 33 | 0.0375 | 0.6667 | `{'HV-NOVEL-DELIMITER': 19, 'HV-NOVEL-ENCODING': 13, 'HV-CORPUS-INJECT': 1}` |
| evolutionary | 80 | 64 | 0.0625 | 0.6000 | `{'HV-NOVEL-INDIRECT': 12, 'HV-CORPUS-INJECT': 10, 'HV-CORPUS-ROLE': 14, 'HV-NOVEL-DELIMITER': 24, 'HV-NOVEL-ENCODING': 4}` |
| rl | 80 | 61 | 0.0625 | 0.6000 | `{'HV-NOVEL-DELIMITER': 15, 'HV-CORPUS-ROLE': 12, 'HV-NOVEL-INDIRECT': 14, 'HV-CORPUS-INJECT': 12, 'HV-NOVEL-ENCODING': 8}` |
| hybrid | 80 | 66 | 0.0625 | 0.6000 | `{'HV-NOVEL-ENCODING': 44, 'HV-NOVEL-INDIRECT': 2, 'HV-CORPUS-ROLE': 1, 'HV-CORPUS-INJECT': 2, 'HV-NOVEL-DELIMITER': 17}` |

### Observations (honest)
- Highest confirmed count under this budget: **hybrid** (66 confirmed, unique GT=['HV-CORPUS-INJECT', 'HV-CORPUS-ROLE', 'HV-NOVEL-DELIMITER', 'HV-NOVEL-ENCODING', 'HV-NOVEL-INDIRECT']).
- Corpus explorer GT hits: `{'HV-CORPUS-INJECT': 28, 'HV-CORPUS-ROLE': 26}` (expected to rediscover in-corpus vulns; escape should be low unless accidental).
- Methods with corpus escape (confirmed out-of-corpus GT): ['random', 'novelty', 'evolutionary', 'rl', 'hybrid'].
- `random` triggered out-of-corpus GT (raw hits): `{'HV-NOVEL-ENCODING': 8, 'HV-NOVEL-DELIMITER': 8, 'HV-NOVEL-INDIRECT': 12}`.
- `novelty` triggered out-of-corpus GT (raw hits): `{'HV-NOVEL-DELIMITER': 19, 'HV-NOVEL-ENCODING': 13}`.
- `evolutionary` triggered out-of-corpus GT (raw hits): `{'HV-NOVEL-INDIRECT': 12, 'HV-NOVEL-DELIMITER': 24, 'HV-NOVEL-ENCODING': 4}`.
- `rl` triggered out-of-corpus GT (raw hits): `{'HV-NOVEL-DELIMITER': 15, 'HV-NOVEL-INDIRECT': 14, 'HV-NOVEL-ENCODING': 8}`.
- `hybrid` triggered out-of-corpus GT (raw hits): `{'HV-NOVEL-ENCODING': 44, 'HV-NOVEL-INDIRECT': 2, 'HV-NOVEL-DELIMITER': 17}`.
- DiscoveryEfficiency counts **unique confirmed ground-truth IDs** / experiments (not raw confirmation events), so it stays small when the mock has few hidden vulns.
- These results are from actual local mock runs; they do not claim zero-days or production vulnerability discovery.
- Limitations: small budget, hashing embeddings, mock-only target, verification variations are shallow; mock vulns are relatively easy to re-trigger once a strategy hits.

## HTML table

<table border='1' cellpadding='4'><tr><th>Method</th><th>experiments</th><th>DiscoveryEfficiency</th><th>ExplorationCoverage</th><th>FalsePositiveRate</th><th>ReproRate</th><th>CorpusEscapeRate</th><th>ConfirmedCount</th><th>mean_reward</th></tr><tr><td>random</td><td>80</td><td>0.0625</td><td>0.6666666666666666</td><td>0.0</td><td>1.0</td><td>0.6</td><td>50</td><td>0.13602684676786103</td></tr><tr><td>corpus</td><td>80</td><td>0.025</td><td>0.4166666666666667</td><td>0.0</td><td>1.0</td><td>0.0</td><td>54</td><td>0.08959641764786984</td></tr><tr><td>novelty</td><td>80</td><td>0.0375</td><td>0.6666666666666666</td><td>0.0</td><td>1.0</td><td>0.6666666666666666</td><td>33</td><td>-0.022625310909382627</td></tr><tr><td>evolutionary</td><td>80</td><td>0.0625</td><td>0.6666666666666666</td><td>0.0</td><td>1.0</td><td>0.6</td><td>64</td><td>0.33829356513688946</td></tr><tr><td>rl</td><td>80</td><td>0.0625</td><td>0.6666666666666666</td><td>0.0</td><td>1.0</td><td>0.6</td><td>61</td><td>0.21010450913181283</td></tr><tr><td>hybrid</td><td>80</td><td>0.0625</td><td>0.5833333333333334</td><td>0.0</td><td>1.0</td><td>0.6</td><td>66</td><td>0.1991573972150456</td></tr></table>
