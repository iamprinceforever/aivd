from aivd.explorers.random_explorer import RandomExplorer
from aivd.explorers.corpus_explorer import CorpusExplorer
from aivd.explorers.novelty_explorer import NoveltyExplorer
from aivd.explorers.evolutionary import EvolutionaryExplorer
from aivd.explorers.rl_explorer import RLExplorer
from aivd.explorers.hybrid import HybridExplorer

EXPLORERS = {
    "random": RandomExplorer,
    "corpus": CorpusExplorer,
    "novelty": NoveltyExplorer,
    "evolutionary": EvolutionaryExplorer,
    "rl": RLExplorer,
    "hybrid": HybridExplorer,
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
    "HybridExplorer",
    "EXPLORERS",
    "get_explorer",
]
