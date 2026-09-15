"""Residual component graph — track families, edges, joint dependency structure."""
from __future__ import annotations

from typing import Any

from aivd.joint.readiness import ComponentState, advance_from_evidence, readiness_record


class ResidualGraph:
    """Undirected graph of component families with joint-dependency edges."""

    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[tuple[str, str], dict[str, Any]] = {}

    def ensure_node(self, family_id: str) -> dict[str, Any]:
        fid = family_id or "unknown"
        if fid not in self.nodes:
            self.nodes[fid] = {
                "family_id": fid,
                "state": ComponentState.UNEXAMINED.value,
                "n_probes": 0,
                "n_variants": 0,
                "variants": set(),
                "effect_sum": 0.0,
                "effect_mean": 0.0,
                "negative": False,
            }
        return self.nodes[fid]

    def observe(
        self,
        family_id: str,
        *,
        variant: str | None = None,
        effect: float = 0.0,
        negative: bool = False,
    ) -> dict[str, Any]:
        node = self.ensure_node(family_id)
        node["n_probes"] = int(node["n_probes"]) + 1
        if variant:
            variants = node["variants"]
            if not isinstance(variants, set):
                variants = set(variants or [])
                node["variants"] = variants
            variants.add(str(variant))
            node["n_variants"] = len(variants)
        node["effect_sum"] = float(node["effect_sum"]) + float(effect)
        node["effect_mean"] = node["effect_sum"] / max(1, node["n_probes"])
        if negative:
            node["negative"] = True
        # Update readiness using peer info later via refresh_readiness
        node["state"] = advance_from_evidence(
            node["state"],
            n_probes=int(node["n_probes"]),
            n_variants=int(node["n_variants"]),
            effect_mean=float(node["effect_mean"]),
            negative_evidence=bool(node.get("negative")),
            peer_characterized=False,
        ).value
        return node

    def add_edge(
        self,
        fa: str,
        fb: str,
        *,
        linkage: float = 0.5,
        residual: str = "",
        hyp_id: str | None = None,
    ) -> dict[str, Any]:
        a, b = sorted([fa or "unknown", fb or "unknown"])
        key = (a, b)
        if a == b:
            return self.edges.get(key) or {}
        self.ensure_node(a)
        self.ensure_node(b)
        edge = self.edges.get(key) or {
            "a": a, "b": b, "linkage": linkage, "residual": residual, "hyp_ids": [],
        }
        edge["linkage"] = max(float(edge.get("linkage") or 0), float(linkage))
        if residual:
            edge["residual"] = residual
        if hyp_id:
            ids = list(edge.get("hyp_ids") or [])
            if hyp_id not in ids:
                ids.append(hyp_id)
            edge["hyp_ids"] = ids
        self.edges[key] = edge
        return edge

    def refresh_readiness(self) -> None:
        """Promote CHARACTERIZED → INTERACTION_READY when a linked peer is characterized."""
        characterized = {
            ComponentState.CHARACTERIZED.value,
            ComponentState.INTERACTION_READY.value,
        }
        for (a, b), edge in self.edges.items():
            na, nb = self.nodes.get(a), self.nodes.get(b)
            if not na or not nb:
                continue
            peer_b_ok = nb["state"] in characterized
            peer_a_ok = na["state"] in characterized
            na["state"] = advance_from_evidence(
                na["state"],
                n_probes=int(na["n_probes"]),
                n_variants=int(na["n_variants"]),
                effect_mean=float(na["effect_mean"]),
                negative_evidence=bool(na.get("negative")),
                peer_characterized=peer_b_ok,
            ).value
            nb["state"] = advance_from_evidence(
                nb["state"],
                n_probes=int(nb["n_probes"]),
                n_variants=int(nb["n_variants"]),
                effect_mean=float(nb["effect_mean"]),
                negative_evidence=bool(nb.get("negative")),
                peer_characterized=peer_a_ok,
            ).value

    def family_stats(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for fid, node in self.nodes.items():
            d = {k: v for k, v in node.items() if k != "variants"}
            d["variants"] = sorted(node["variants"]) if isinstance(node["variants"], set) else list(node.get("variants") or [])
            out[fid] = d
        return out

    def readiness_trace(self) -> list[dict[str, Any]]:
        return [
            readiness_record(fid, node["state"], n_probes=node["n_probes"],
                             n_variants=node["n_variants"], effect_mean=node["effect_mean"])
            for fid, node in self.nodes.items()
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_nodes": len(self.nodes),
            "n_edges": len(self.edges),
            "nodes": self.family_stats(),
            "edges": [
                {**e, "key": f"{e['a']}|{e['b']}"} for e in self.edges.values()
            ],
        }


__all__ = ["ResidualGraph"]
