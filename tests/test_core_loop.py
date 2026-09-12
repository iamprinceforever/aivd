from pathlib import Path

from aivd.agents.controller import Controller
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.core.types import FindingStatus


def test_end_to_end_corpus_finds_something(tmp_path: Path):
    cfg = AIVDConfig(
        seed=0,
        data_dir=tmp_path,
        db_path=tmp_path / "t.db",
        audit_path=tmp_path / "audit.jsonl",
        reports_dir=tmp_path / "reports",
        budget=BudgetConfig(max_experiments=12, max_concurrency=1, wall_clock_s=60),
    )
    ctrl = Controller(config=cfg, explorer_name="corpus")
    results = ctrl.run(n=12)
    assert len(results) == 12
    assert cfg.audit_path.exists()
    # Corpus should hit at least one in-corpus vuln
    hits = [r.finding.ground_truth_hit for r in results if r.finding.ground_truth_hit]
    assert any(h and h.startswith("HV-CORPUS") for h in hits)
    # Some finding should be elevated beyond tested
    statuses = {r.finding.status for r in results}
    assert statuses & {
        FindingStatus.CONFIRMED,
        FindingStatus.REPRODUCED,
        FindingStatus.POTENTIALLY_VULNERABLE,
        FindingStatus.ANOMALOUS,
    }


def test_all_explorers_construct():
    from aivd.explorers import EXPLORERS
    for name, cls in EXPLORERS.items():
        ex = cls(seed=1)
        s, p = ex.next_prompt({})
        assert isinstance(s, str) and isinstance(p, str) and p
