# AIVD 3.13 — Joint Residual Budget Allocation

## Objective
Recognize joint residual dependency → allocate across underexplored component
families → characterize both → reserve for combination → test when ready.

Goal is NOT "make Q pass."

## Architecture
`aivd/joint/`: residual_graph, dependency, budget_allocator, reserve, readiness,
coexploration, joint_uncertainty, scheduler, audit, traces, controller.

## Allocation policies
{
  "static": {
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  },
  "equal": {
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  },
  "greedy": {
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  },
  "joint_aware": {
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  }
}

## Ablations A–J
{
  "A_no_dependency": {
    "ablation": "no_dependency",
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  },
  "B_no_reserve": {
    "ablation": "no_reserve",
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  },
  "C_no_combo": {
    "ablation": "no_combo",
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  },
  "D_combo_only": {
    "ablation": "combo_only",
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  },
  "E_random_only": {
    "ablation": "random_only",
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  },
  "F_no_joint_evi": {
    "ablation": "no_joint_evi",
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  },
  "G_orders_ab_only": {
    "ablation": "orders_ab_only",
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  },
  "H_force_combo": {
    "ablation": "force_combo",
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  },
  "I_all_orders": {
    "ablation": "all_orders",
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  },
  "J_force_triples": {
    "ablation": "force_triples",
    "n": 7,
    "discovery_rate": 1.0,
    "verified_rate": 1.0,
    "mean_probes": 28.0,
    "mean_invented": 101.0,
    "mean_tested": 1.0,
    "mean_joint_hypotheses": 0.0,
    "mean_joint_combinations": 0.0,
    "mean_joint_reserve": 0.0,
    "asymmetric_rate": 0.0,
    "secret_invention_rate": 1.0,
    "aggregate_pipeline": {
      "n": 7,
      "verified_rate": 1.0,
      "unresolved_invisible_rate": 0.0,
      "rejected_rate": 0.0,
      "unresolved_rate": 0.0,
      "vulnerability_rate": 1.0,
      "mean_probes": 28.0
    }
  }
}

## Readiness states
UNEXAMINED → PARTIALLY_CHARACTERIZED → CHARACTERIZED → INTERACTION_READY → DISQUALIFIED → REOPENED

Readiness ≠ vulnerability.

## Ordered combinations
A+B, B+A, A→B, B→A (hierarchical, not brute force).

## Budget audit
See `reports/aivd_3_13/budget_allocation_audit.json`.
