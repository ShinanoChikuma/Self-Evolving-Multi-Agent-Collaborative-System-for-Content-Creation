"""LlamaIndex 驱动的语义检索器 —— 替代原 TfIdfEngine。

使用 BGE 中文 Embedding + ChromaDB 向量存储，
保持与旧 Retriever 完全相同的对外接口。
"""

from __future__ import annotations

import os
from typing import Any

import chromadb
from llama_index.core import Settings

from .embeddings import BGEEmbedding

# ChromaDB 持久化目录（相对于 data/）
_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")


class LlamaRetriever:
    """语义检索器 —— 完全兼容旧 Retriever 接口。"""

    def __init__(self, persist_dir: str = _PERSIST_DIR) -> None:
        # 设置 LlamaIndex 全局 embedding 模型（仅首次）
        if not hasattr(Settings, "_bg_embed_set") or not Settings._bg_embed_set:
            Settings.embed_model = BGEEmbedding()
            Settings._bg_embed_set = True  # type: ignore[attr-defined]

        self._embed_model = Settings.embed_model
        self._chroma_client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._chroma_client.get_or_create_collection(
            name="runs",
            metadata={"hnsw:space": "cosine"},
        )
        self._doc_meta: dict[str, dict[str, Any]] = {}

    # ── 索引管理 ────────────────────────────────────────

    def index_runs(self, runs: list[dict[str, Any]]) -> None:
        """全量重建索引（启动时调用）。"""
        self._doc_meta.clear()

        if not runs:
            return

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        embeddings: list[list[float]] = []

        for run in runs:
            run_id = run.get("id", "")
            if not run_id:
                continue

            text = self._make_searchable_text(run)
            if not text.strip():
                continue

            ids.append(run_id)
            documents.append(text)
            metadatas.append(self._make_metadata(run))
            self._doc_meta[run_id] = self._make_full_meta(run)

        if ids:
            # 清空旧数据后批量插入
            try:
                self._collection.delete(where={})
            except Exception:
                pass

            # 计算 embeddings
            embeddings = self._embed_model._get_text_embeddings(documents)  # type: ignore[assignment]

            self._collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )

    def add_run(self, run: dict[str, Any]) -> None:
        """增量添加一条记录到索引。"""
        run_id = run.get("id", "")
        if not run_id:
            return

        text = self._make_searchable_text(run)
        if not text.strip():
            return

        embedding = self._embed_model._get_text_embedding(text)

        # 先尝试删除旧记录（幂等更新）
        try:
            self._collection.delete(ids=[run_id])
        except Exception:
            pass

        self._collection.add(
            ids=[run_id],
            documents=[text],
            metadatas=[self._make_metadata(run)],
            embeddings=[embedding],
        )
        self._doc_meta[run_id] = self._make_full_meta(run)

    def remove_run(self, run_id: str) -> bool:
        """从索引中移除一条记录。"""
        self._doc_meta.pop(run_id, None)
        try:
            self._collection.delete(ids=[run_id])
            return True
        except Exception:
            return False

    # ── 检索 ────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        content_type: str = "",
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """语义检索最相关的历史案例。"""
        query_embedding = self._embed_model._get_query_embedding(query)

        where: dict[str, Any] | None = None
        if content_type:
            where = {"content_type": content_type}

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["metadatas", "distances"],
            )
        except Exception:
            return []

        ids = results.get("ids", [[]])[0]
        if not ids:
            return []

        items: list[dict[str, Any]] = []
        for doc_id in ids:
            meta = self._doc_meta.get(doc_id)
            if meta:
                items.append(meta)
        return items

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

    # ── 内部工具 ────────────────────────────────────────

    @staticmethod
    def _make_searchable_text(run: dict[str, Any]) -> str:
        """构建用于 embedding 的搜索文本。"""
        return " ".join(
            filter(None, [
                run.get("content_type", ""),
                run.get("user_prompt", ""),
                run.get("audience", ""),
                run.get("tone", ""),
                run.get("final_content", "")[:800],
            ])
        )

    @staticmethod
    def _make_metadata(run: dict[str, Any]) -> dict[str, Any]:
        """构建 ChromaDB metadata（有类型约束，不含过长文本）。"""
        return {
            "content_type": run.get("content_type", ""),
            "tone": run.get("tone", ""),
            "audience": run.get("audience", ""),
            "mode": run.get("mode", ""),
            "user_prompt": run.get("user_prompt", "")[:200],
        }

    @staticmethod
    def _make_full_meta(run: dict[str, Any]) -> dict[str, Any]:
        """构建完整元数据（保留在内存中，用于 retrieve 返回）。"""
        return {
            "id": run.get("id", ""),
            "content_type": run.get("content_type", ""),
            "user_prompt": run.get("user_prompt", ""),
            "tone": run.get("tone", ""),
            "audience": run.get("audience", ""),
            "final_content": run.get("final_content", ""),
            "mode": run.get("mode", ""),
        }

    @property
    def doc_count(self) -> int:
        try:
            return self._collection.count()
        except Exception:
            return 0
