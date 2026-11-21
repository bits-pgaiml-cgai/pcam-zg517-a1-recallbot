import math
import re
from collections import Counter
from typing import Iterable, List, Sequence


TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)?", re.I)


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]


class BM25:
    def __init__(self, corpus: Sequence[Sequence[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = [list(doc) for doc in corpus]
        self.N = len(self.corpus)
        self.doc_lens = [len(doc) for doc in self.corpus]
        self.avgdl = (sum(self.doc_lens) / self.N) if self.N else 0.0
        self.df = Counter()
        for doc in self.corpus:
            for term in set(doc):
                self.df[term] += 1
        self.tf = [Counter(doc) for doc in self.corpus]

    def idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log((self.N - df + 0.5) / (df + 0.5) + 1.0)

    def score(self, query: Sequence[str], doc_index: int) -> float:
        doc_tf = self.tf[doc_index]
        dl = self.doc_lens[doc_index]
        norm = 1.0 - self.b + self.b * (dl / self.avgdl) if self.avgdl else 1.0
        total = 0.0
        for term in query:
            f = doc_tf.get(term, 0)
            if f == 0:
                continue
            tf_comp = (f * (self.k1 + 1.0)) / (f + self.k1 * norm)
            total += self.idf(term) * tf_comp
        return total

    def score_document_tokens(self, query: Sequence[str], doc_tokens: Sequence[str]) -> float:
        doc_tf = Counter(doc_tokens)
        dl = len(doc_tokens)
        norm = 1.0 - self.b + self.b * (dl / self.avgdl) if self.avgdl else 1.0
        total = 0.0
        for term in query:
            f = doc_tf.get(term, 0)
            if f == 0:
                continue
            tf_comp = (f * (self.k1 + 1.0)) / (f + self.k1 * norm)
            total += self.idf(term) * tf_comp
        return total

    def get_scores(self, query: Sequence[str]) -> List[float]:
        return [self.score(query, i) for i in range(self.N)]

    def rank(self, query_text: str, top_k: int = 10) -> List[tuple]:
        q = tokenize(query_text)
        scores = self.get_scores(q)
        order = sorted(range(self.N), key=lambda i: scores[i], reverse=True)
        return [(i, scores[i]) for i in order[:top_k]]


def bm25_cs4_worked_example_score() -> float:
    """Reproduce CS4 slide BM25 example. Slide shows 4.159; exact arithmetic is ~4.160.

    Slide inputs: N=1000, avgdl=50, |D|=12, k1=1.5, b=0.75,
    query terms machine (df=300,f=2) and learning (df=400,f=3).
    """
    N = 1000
    avgdl = 50.0
    k1 = 1.5
    b = 0.75
    doc_len = 12
    q_terms = [("machine", 2, 300), ("learning", 3, 400)]
    norm = 1 - b + b * (doc_len / avgdl)
    total = 0.0
    for term, f, df in q_terms:
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
        tf_comp = (f * (k1 + 1.0)) / (f + k1 * norm)
        total += idf * tf_comp
    return total
