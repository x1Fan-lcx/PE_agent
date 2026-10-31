"""嵌入层抽象：RAG 用。

设计取舍：真实语义嵌入需要外部 API（如 text-embedding-v3），
为了离线可跑、CI 可测，提供 HashingEmbedder（确定性词袋哈希，无语义、仅演示链路）。
生产切 OpenAIEmbedder 只需配 .env 的 EMBED_API_KEY。
"""
from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from typing import Any

from pe_agent.config import get_settings

_EMBED_DIM = 256


class Embedder(ABC):
    @abstractmethod
    def embed_query(self, text: str) -> list[float]: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]


class HashingEmbedder(Embedder):
    """词袋哈希向量：把文本切词后哈希到固定维度，归一化。离线可用，仅演示。"""

    def embed_query(self, text: str) -> list[float]:
        vec = [0.0] * _EMBED_DIM
        tokens = re.findall(r"[\u4e00-\u9fa5]|[a-zA-Z0-9]+", text.lower())
        for t in tokens:
            h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
            vec[h % _EMBED_DIM] += 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]


class OpenAIEmbedder(Embedder):
    """OpenAI 兼容语义嵌入。"""

    def __init__(self) -> None:
        s = get_settings()
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("需要 langchain-openai 依赖") from e
        self._emb = OpenAIEmbeddings(
            model=s.embed_model,
            api_key=s.embed_api_key,
            base_url=s.embed_api_base or None,
        )

    def embed_query(self, text: str) -> list[float]:
        return self._emb.embed_query(text)


def get_embedder() -> Embedder:
    s = get_settings()
    if s.embed_api_key:
        return OpenAIEmbedder()
    return HashingEmbedder()
