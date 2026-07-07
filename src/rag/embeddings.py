"""BGE 中文 Embedding 模型 —— LlamaIndex 兼容封装。

使用 BAAI/bge-small-zh-v1.5，专为中文语义检索优化，约 100MB。
首次使用自动下载，之后从缓存加载。
"""

from __future__ import annotations

from typing import Any, List

from llama_index.core.embeddings import BaseEmbedding
from sentence_transformers import SentenceTransformer


class BGEEmbedding(BaseEmbedding):
    """BGE 中文 Embedding，通过 sentence-transformers 加载。"""

    _model: SentenceTransformer

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-zh-v1.5",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._model = SentenceTransformer(model_name)

    @classmethod
    def class_name(cls) -> str:
        return "BGEEmbedding"

    def _get_query_embedding(self, query: str) -> List[float]:
        # BGE 模型建议对 query 加前缀以提升检索质量
        if not query.startswith("为这个句子生成表示以用于检索相关文章："):
            query = "为这个句子生成表示以用于检索相关文章：" + query
        return self._model.encode(
            query, normalize_embeddings=True, show_progress_bar=False,
        ).tolist()

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._model.encode(
            text, normalize_embeddings=True, show_progress_bar=False,
        ).tolist()

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)
