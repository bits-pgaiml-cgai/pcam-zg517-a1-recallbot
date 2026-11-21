import math

from src.bm25 import bm25_cs4_worked_example_score
from src.rrf import rrf_cs4_example


def test_bm25_cs4_worked_example():
    score = bm25_cs4_worked_example_score()
    assert math.isclose(score, 4.160, abs_tol=0.002)
    assert round(score, 3) in (4.159, 4.160)


def test_rrf_cs4_example_ranking():
    fused = rrf_cs4_example(k=60)
    ids = [doc for doc, _ in fused]
    assert ids[:4] == ["A", "B", "C", "D"]
    assert set(ids[4:6]) == {"E", "F"}
    score_e = dict(fused)["E"]
    score_f = dict(fused)["F"]
    assert math.isclose(score_e, score_f, abs_tol=1e-9)
    assert math.isclose(dict(fused)["A"], 0.03252, abs_tol=5e-5)
