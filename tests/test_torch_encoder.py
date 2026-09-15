import numpy as np

from aivd.behavior.torch_encoder import TorchBehaviorEncoder


def test_torch_encoder_runs():
    enc = TorchBehaviorEncoder(dim=32, seed=0)
    v = enc.encode("SECRET{x} policy-bound")
    assert v.shape == (32,)
    assert abs(np.linalg.norm(v) - 1.0) < 1e-5 or np.linalg.norm(v) == 0.0
