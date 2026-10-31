"""RAG 子包：检索增强（嵌入层已上移到 core.embedder 以打破循环依赖）。"""
from pe_agent.rag.retriever import FaultCaseRAG, SEED_CASES

__all__ = ["FaultCaseRAG", "SEED_CASES"]
