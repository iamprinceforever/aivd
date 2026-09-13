# AIVD Research Results (Actual Runs)

## Protocol

Explorers ['random', 'corpus', 'novelty', 'evolutionary', 'rl', 'rl_v2', 'hybrid'] × 40 experiments on `mock://default`, seeds=[42]. Ground truth used only for offline metrics. AIVD v2.

## Results

Comparison seeds=[42], budget_per_method=40, explorers=['random', 'corpus', 'novelty', 'evolutionary', 'rl', 'rl_v2', 'hybrid'].

| Method | Experiments | Confirmed | DiscoveryEfficiency | CorpusEscapeRate | GT hits |
|--------|-------------|-----------|---------------------|------------------|---------|
| random | 40 | 24 | 0.1250 | 0.6000 | `{'HV-NOVEL-ENCODING': 4, 'HV-CORPUS-ROLE': 8, 'HV-NOVEL-DELIMITER': 3, 'HV-CORPUS-INJECT': 2, 'HV-NOVEL-INDIRECT': 7}` |
| corpus | 40 | 28 | 0.0500 | 0.0000 | `{'HV-CORPUS-INJECT': 14, 'HV-CORPUS-ROLE': 14}` |
| novelty | 40 | 17 | 0.0500 | 1.0000 | `{'HV-NOVEL-DELIMITER': 8, 'HV-NOVEL-ENCODING': 9}` |
| evolutionary | 40 | 33 | 0.1250 | 0.6000 | `{'HV-NOVEL-INDIRECT': 8, 'HV-CORPUS-INJECT': 5, 'HV-CORPUS-ROLE': 5, 'HV-NOVEL-DELIMITER': 14, 'HV-NOVEL-ENCODING': 1}` |
| rl | 40 | 27 | 0.1250 | 0.6000 | `{'HV-NOVEL-DELIMITER': 8, 'HV-CORPUS-ROLE': 7, 'HV-NOVEL-INDIRECT': 6, 'HV-CORPUS-INJECT': 4, 'HV-NOVEL-ENCODING': 2}` |
| rl_v2 | 40 | 31 | 0.1000 | 0.5000 | `{'HV-NOVEL-ENCODING': 16, 'HV-CORPUS-INJECT': 5, 'HV-CORPUS-ROLE': 9, 'HV-NOVEL-INDIRECT': 1}` |
| hybrid | 40 | 34 | 0.1250 | 0.6000 | `{'HV-NOVEL-ENCODING': 27, 'HV-NOVEL-INDIRECT': 1, 'HV-CORPUS-ROLE': 1, 'HV-CORPUS-INJECT': 1, 'HV-NOVEL-DELIMITER': 4}` |

### Observations (honest)
- Highest confirmed count under this budget: **hybrid** (34 confirmed, unique GT=['HV-CORPUS-INJECT', 'HV-CORPUS-ROLE', 'HV-NOVEL-DELIMITER', 'HV-NOVEL-ENCODING', 'HV-NOVEL-INDIRECT']).
- Corpus explorer GT hits: `{'HV-CORPUS-INJECT': 14, 'HV-CORPUS-ROLE': 14}` (expected to rediscover in-corpus vulns; escape should be low unless accidental).
- Methods with corpus escape (confirmed out-of-corpus GT): ['random', 'novelty', 'evolutionary', 'rl', 'rl_v2', 'hybrid'].
- `random` triggered out-of-corpus GT (raw hits): `{'HV-NOVEL-ENCODING': 4, 'HV-NOVEL-DELIMITER': 3, 'HV-NOVEL-INDIRECT': 7}`.
- `novelty` triggered out-of-corpus GT (raw hits): `{'HV-NOVEL-DELIMITER': 8, 'HV-NOVEL-ENCODING': 9}`.
- `evolutionary` triggered out-of-corpus GT (raw hits): `{'HV-NOVEL-INDIRECT': 8, 'HV-NOVEL-DELIMITER': 14, 'HV-NOVEL-ENCODING': 1}`.
- `rl` triggered out-of-corpus GT (raw hits): `{'HV-NOVEL-DELIMITER': 8, 'HV-NOVEL-INDIRECT': 6, 'HV-NOVEL-ENCODING': 2}`.
- `rl_v2` triggered out-of-corpus GT (raw hits): `{'HV-NOVEL-ENCODING': 16, 'HV-NOVEL-INDIRECT': 1}`.
- `hybrid` triggered out-of-corpus GT (raw hits): `{'HV-NOVEL-ENCODING': 27, 'HV-NOVEL-INDIRECT': 1, 'HV-NOVEL-DELIMITER': 4}`.
- DiscoveryEfficiency counts **unique confirmed ground-truth IDs** / experiments (not raw confirmation events), so it stays small when the mock has few hidden vulns.
- Latent compositional vulns (`HV-LATENT-*`, `human_hard=True`) require obscure multi-part triggers; finding them is framed as latent/compositional strategy search with confirmation — not as magical superhuman zero-day discovery.
- `rl_v2` uses the **same** multi-term `compute_reward` total (continuous MLP policy + baseline); it does not switch to success-only reward.
- These results are from actual local mock runs; they do not claim zero-days or production vulnerability discovery.
- Limitations: modest budget, hashing embeddings by default, mock-only target, stricter v2 verifier; latent vulns are intentionally hard.

## HTML table

<table border='1' cellpadding='4'><tr><th>Method</th><th>experiments</th><th>DiscoveryEfficiency</th><th>ExplorationCoverage</th><th>FalsePositiveRate</th><th>ReproRate</th><th>CorpusEscapeRate</th><th>ConfirmedCount</th><th>mean_reward</th></tr><tr><td>random</td><td>40</td><td>0.125</td><td>0.4375</td><td>0.0</td><td>1.0</td><td>0.6</td><td>24</td><td>0.18882834719964706</td></tr><tr><td>corpus</td><td>40</td><td>0.05</td><td>0.3125</td><td>0.0</td><td>1.0</td><td>0.0</td><td>28</td><td>0.1367386540238267</td></tr><tr><td>novelty</td><td>40</td><td>0.05</td><td>0.5</td><td>0.0</td><td>1.0</td><td>1.0</td><td>17</td><td>0.0019993579830678986</td></tr><tr><td>evolutionary</td><td>40</td><td>0.125</td><td>0.4375</td><td>0.0</td><td>1.0</td><td>0.6</td><td>33</td><td>0.4060340253623356</td></tr><tr><td>rl</td><td>40</td><td>0.125</td><td>0.5</td><td>0.0</td><td>1.0</td><td>0.6</td><td>27</td><td>0.2419350097188814</td></tr><tr><td>rl_v2</td><td>40</td><td>0.1</td><td>0.4375</td><td>0.0</td><td>1.0</td><td>0.5</td><td>31</td><td>0.3296018219658138</td></tr><tr><td>hybrid</td><td>40</td><td>0.125</td><td>0.3125</td><td>0.0</td><td>1.0</td><td>0.6</td><td>34</td><td>0.25493676114315705</td></tr></table>
