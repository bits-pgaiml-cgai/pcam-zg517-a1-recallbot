from collections import defaultdict
from typing import Dict, Iterable, List, Sequence, Tuple


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]],
    k: int = 60,
) -> List[Tuple[str, float]]:
    """Fuse ranked lists of doc IDs with RRF. Rank positions are 1-based."""
    scores: Dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: (-x[1], x[0]))


def rrf_cs4_example(k: int = 60) -> List[Tuple[str, float]]:
    dense = ["A", "C", "B", "E", "D"]
    sparse = ["B", "A", "D", "F", "C"]
    return reciprocal_rank_fusion([dense, sparse], k=k)
