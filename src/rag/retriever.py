"""RAG 检索层 — 基于 TF-IDF 的无依赖检索 + 上下文构建。

职责：
- 索引历史创作记录
- 根据当前创作需求检索最相关的历史案例
- 构建注入 Agent 的上下文片段
- 管理知识库条目的检索
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any


# ── 中文分词工具（轻量级，无外部依赖）─────────────────────

_CHAR_PATTERN = re.compile(r"[一-鿿]+|[a-zA-Z0-9]+")


def _tokenize(text: str) -> list[str]:
    """简单的中英文混合分词：中文按单字+双字组合，英文按词切分。"""
    tokens: list[str] = []
    for match in _CHAR_PATTERN.finditer(text.lower()):
        segment = match.group()
        if re.search(r"[一-鿿]", segment):
            # 中文：单字 + 双字 n-gram
            tokens.extend(segment)
            tokens.extend(segment[i : i + 2] for i in range(len(segment) - 1))
        else:
            # 英文/数字：直接作为词
            if len(segment) >= 2:
                tokens.append(segment)
    return tokens


# ── TF-IDF 引擎 ────────────────────────────────────────────

class TfIdfEngine:
    """纯 Python TF-IDF 实现，无外部依赖。"""

    def __init__(self) -> None:
        self._docs: dict[str, str] = {}         # doc_id -> raw text
        self._doc_terms: dict[str, list[str]] = {}  # doc_id -> token list
        self._df: dict[str, int] = defaultdict(int)  # term -> document frequency
        self._doc_count = 0

    @property
    def doc_ids(self) -> list[str]:
        return list(self._docs.keys())

    def add(self, doc_id: str, text: str) -> None:
        """添加或更新文档。"""
        tokens = _tokenize(text)
        # 去重统计 DF
        unique_terms = set(tokens)
        for term in unique_terms:
            self._df[term] += 1
        self._docs[doc_id] = text
        self._doc_terms[doc_id] = tokens
        self._doc_count += 1

    def remove(self, doc_id: str) -> bool:
        """移除文档。"""
        if doc_id not in self._docs:
            return False
        unique_terms = set(self._doc_terms.get(doc_id, []))
        for term in unique_terms:
            if self._df.get(term, 0) > 0:
                self._df[term] -= 1
                if self._df[term] <= 0:
                    del self._df[term]
        del self._docs[doc_id]
        del self._doc_terms[doc_id]
        self._doc_count -= 1
        return True

    def rebuild(self, documents: dict[str, str]) -> None:
        """全量重建索引。"""
        self._docs.clear()
        self._doc_terms.clear()
        self._df.clear()
        self._doc_count = 0
        for doc_id, text in documents.items():
            self.add(doc_id, text)

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """检索 top_k 最相关文档，返回 [(doc_id, score), ...]."""
        if not self._docs or top_k <= 0:
            return []

        query_terms = _tokenize(query)
        if not query_terms:
            return []

        # 计算 query TF
        query_tf: dict[str, float] = {}
        for t in query_terms:
            query_tf[t] = query_tf.get(t, 0) + 1
        query_len = len(query_terms)
        for t in query_tf:
            query_tf[t] /= query_len

        # 计算每个文档的余弦相似度
        scores: list[tuple[str, float]] = []
        for doc_id, terms in self._doc_terms.items():
            score = self._cosine_similarity(query_tf, terms)
            if score > 0:
                scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _cosine_similarity(self, query_tf: dict[str, float], doc_terms: list[str]) -> float:
        """计算 query 与文档的余弦相似度。"""
        # 文档 TF
        doc_tf: dict[str, float] = {}
        doc_len = len(doc_terms)
        if doc_len == 0:
            return 0.0
        for t in doc_terms:
            doc_tf[t] = doc_tf.get(t, 0) + 1
        for t in doc_tf:
            doc_tf[t] /= doc_len

        # 点积（带 IDF 加权）
        dot = 0.0
        for term, q_weight in query_tf.items():
            if term in doc_tf:
                idf = math.log((self._doc_count + 1) / (self._df.get(term, 0) + 1)) + 1
                dot += q_weight * idf * doc_tf[term] * idf

        # 文档向量模长
        doc_norm = 0.0
        for term, tf in doc_tf.items():
            idf = math.log((self._doc_count + 1) / (self._df.get(term, 0) + 1)) + 1
            doc_norm += (tf * idf) ** 2
        doc_norm = math.sqrt(doc_norm) if doc_norm > 0 else 1.0

        # query 向量模长
        query_norm = 0.0
        for term, tf in query_tf.items():
            idf = math.log((self._doc_count + 1) / (self._df.get(term, 0) + 1)) + 1
            query_norm += (tf * idf) ** 2
        query_norm = math.sqrt(query_norm) if query_norm > 0 else 1.0

        return dot / (doc_norm * query_norm) if (doc_norm * query_norm) > 0 else 0.0


# ── 检索器 ─────────────────────────────────────────────────

class Retriever:
    """RAG 检索器：统一管理历史案例索引与知识库检索。"""

    def __init__(self) -> None:
        self._engine = TfIdfEngine()
        self._doc_meta: dict[str, dict[str, Any]] = {}  # doc_id -> metadata
        self._initialized = False

    # ── 索引管理 ────────────────────────────────────────

    def index_runs(self, runs: list[dict[str, Any]]) -> None:
        """索引历史创作记录。"""
        documents: dict[str, str] = {}
        self._doc_meta.clear()

        for run in runs:
            run_id = run.get("id", "")
            if not run_id:
                continue

            # 拼接可检索文本
            searchable = " ".join(
                filter(None, [
                    run.get("content_type", ""),
                    run.get("user_prompt", ""),
                    run.get("audience", ""),
                    run.get("tone", ""),
                    run.get("final_content", "")[:800],  # 前 800 字
                ])
            )
            if searchable.strip():
                documents[run_id] = searchable
                self._doc_meta[run_id] = {
                    "id": run_id,
                    "content_type": run.get("content_type", ""),
                    "user_prompt": run.get("user_prompt", ""),
                    "tone": run.get("tone", ""),
                    "audience": run.get("audience", ""),
                    "final_content": run.get("final_content", ""),
                    "mode": run.get("mode", ""),
                }

        self._engine.rebuild(documents)
        self._initialized = True

    def add_run(self, run: dict[str, Any]) -> None:
        """增量添加一条记录到索引。"""
        run_id = run.get("id", "")
        if not run_id:
            return
        searchable = " ".join(
            filter(None, [
                run.get("content_type", ""),
                run.get("user_prompt", ""),
                run.get("audience", ""),
                run.get("tone", ""),
                run.get("final_content", "")[:800],
            ])
        )
        if searchable.strip():
            self._engine.add(run_id, searchable)
            self._doc_meta[run_id] = {
                "id": run_id,
                "content_type": run.get("content_type", ""),
                "user_prompt": run.get("user_prompt", ""),
                "tone": run.get("tone", ""),
                "audience": run.get("audience", ""),
                "final_content": run.get("final_content", ""),
                "mode": run.get("mode", ""),
            }

    def remove_run(self, run_id: str) -> None:
        """从索引中移除一条记录。"""
        self._engine.remove(run_id)
        self._doc_meta.pop(run_id, None)

    # ── 检索 ────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        content_type: str = "",
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """检索最相关的历史案例。

        Args:
            query: 当前创作需求文本
            content_type: 按内容类型加权过滤（同类型得分 x1.2）
            top_k: 返回数量

        Returns:
            相关案例列表，按相似度降序
        """
        if not self._initialized:
            return []

        # 扩充 query 以增加召回
        augmented_query = f"{content_type} {query}"
        results = self._engine.search(augmented_query, top_k=top_k * 2)

        # 同类型加权
        scored: list[tuple[dict[str, Any], float]] = []
        for doc_id, score in results:
            meta = self._doc_meta.get(doc_id)
            if meta is None:
                continue
            if content_type and meta.get("content_type") == content_type:
                score *= 1.2
            scored.append((meta, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in scored[:top_k]]

    def retrieve_context(
        self,
        query: str,
        content_type: str = "",
        top_k: int = 3,
    ) -> str:
        """检索并格式化为可直接注入 Agent 的上下文字符串。"""
        results = self.retrieve(query, content_type=content_type, top_k=top_k)
        if not results:
            return "暂无相关历史案例"

        parts: list[str] = []
        for i, item in enumerate(results, 1):
            parts.append(
                f"[案例{i}] {item.get('content_type', '')} | "
                f"需求：{item.get('user_prompt', '')[:100]}\n"
                f"成品摘要：{item.get('final_content', '')[:300]}..."
            )
        return "\n\n".join(parts)

    # ── Knowledge Base ───────────────────────────────────

    def search_knowledge(
        self,
        query: str,
        knowledge_entries: list[dict[str, Any]],
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """在知识库中检索（使用 TF-IDF）。"""
        if not knowledge_entries:
            return []

        # 临时索引
        temp_engine = TfIdfEngine()
        doc_map: dict[str, dict[str, Any]] = {}
        for entry in knowledge_entries:
            eid = entry.get("id", "")
            text = " ".join([
                entry.get("title", ""),
                entry.get("content", ""),
                " ".join(entry.get("tags", [])),
            ])
            if text.strip():
                temp_engine.add(eid, text)
                doc_map[eid] = entry

        results = temp_engine.search(query, top_k=top_k)
        return [doc_map[doc_id] for doc_id, _ in results if doc_id in doc_map]

    @property
    def doc_count(self) -> int:
        return self._engine.doc_count if hasattr(self._engine, 'doc_count') else self._engine._doc_count
