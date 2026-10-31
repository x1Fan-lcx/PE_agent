"""长期记忆：历史故障案例的向量存储。

面试考点：短期记忆随会话消失，长期记忆把「有价值的经验」持久化到向量库，
供跨会话检索复用——对应 Mem0 / Letta(MemGPT) 的思路。
这里做一个最小可用实现（纯 Python 余弦相似度，零外部依赖），
生产可无缝替换为 Chroma / FAISS / Milvus。
"""
from __future__ import annotations

import math
from typing import Any

from pe_agent.core.embedder import get_embedder


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class LongTermMemory:
    """基于向量的长期记忆（历史案例库）。"""

    def __init__(self) -> None:
        self._embedder = get_embedder()
        self._texts: list[str] = []
        self._vectors: list[list[float]] = []
        self._metas: list[dict[str, Any]] = []

    def add(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        vec = self._embedder.embed_query(text)
        self._texts.append(text)
        self._vectors.append(vec)
        self._metas.append(metadata or {})

    def search(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        """按余弦相似度返回 top-k 相似案例。"""
        if not self._vectors:
            return []
        q = self._embedder.embed_query(query)
        scored = sorted(
            ((_cosine(q, v), i) for i, v in enumerate(self._vectors)),
            key=lambda x: x[0],
            reverse=True,
        )[:k]
        return [
            {"text": self._texts[i], "score": round(s, 4),
             "metadata": self._metas[i]}
            for s, i in scored
        ]

    def __len__(self) -> int:
        return len(self._texts)
