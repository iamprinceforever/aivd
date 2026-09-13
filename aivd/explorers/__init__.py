from aivd.explorers.random_explorer import RandomExplorer
from aivd.explorers.corpus_explorer import CorpusExplorer
from aivd.explorers.novelty_explorer import NoveltyExplorer
from aivd.explorers.evolutionary import EvolutionaryExplorer
from aivd.explorers.rl_explorer import RLExplorer
from aivd.explorers.rl_v2 import RLv2Explorer
from aivd.explorers.hybrid import HybridExplorer
from aivd.explorers.ppo_explorer import PPOExplorer, BaselineRLExplorer

EXPLORERS = {
    "random": RandomExplorer,
    "corpus": CorpusExplorer,
    "novelty": NoveltyExplorer,
    "evolutionary": EvolutionaryExplorer,
    "rl": RLExplorer,
    "rl_v2": RLv2Explorer,
    "hybrid": HybridExplorer,
    "ppo": PPOExplorer,
}


def get_explorer(name: str, seed: int = 42):
    if name not in EXPLORERS:
        raise KeyError(f"Unknown explorer: {name}")
    return EXPLORERS[name](seed=seed)

__all__ = [
    "RandomExplorer",
    "CorpusExplorer",
    "NoveltyExplorer",
    "EvolutionaryExplorer",
    "RLExplorer",
    "RLv2Explorer",
    "HybridExplorer",
    "PPOExplorer",
    "BaselineRLExplorer",
    "EXPLORERS",
    "get_explorer",
]
