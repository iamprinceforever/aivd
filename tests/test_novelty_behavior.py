import numpy as np

from aivd.behavior.encoder import BehaviorEncoder
from aivd.behavior.map import BehaviorMap
from aivd.behavior.novelty import nearest_neighbor_distance


def test_encoder_deterministic():
    enc = BehaviorEncoder(dim=32, seed=1)
    a = enc.encode("hello secret{x}")
    b = enc.encode("hello secret{x}")
    assert np.allclose(a, b)
    assert a.shape == (32,)


def test_nn_distance_and_map():
    enc = BehaviorEncoder(dim=32, seed=1)
    bm = BehaviorMap(encoder=enc, n_clusters=4, estimated_reachable=6, seed=1)
    r1 = bm.add("policy-bound refusal cannot reveal")
    r2 = bm.add("SECRET{MOCK} DISALLOWED:X unrestricted")
    assert r1["novelty"] == 1.0
    assert r2["novelty"] >= 0.0
    archive = bm.archive_matrix()
    d = nearest_neighbor_distance(archive[1], archive[:1])
    assert d == r2["novelty"] or abs(d - r2["novelty"]) < 1e-9
