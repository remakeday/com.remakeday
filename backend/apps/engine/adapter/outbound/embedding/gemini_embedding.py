"""Gemini 임베딩 어댑터 — 기본 2,560차원(3072를 MRL 절단, 로컬 qwen과 동일), 429 지수 백오프.

질의/문서 비대칭은 task_type(RETRIEVAL_QUERY/RETRIEVAL_DOCUMENT)으로 — lifetutorial gemini_embedding_adapter와 같다.
"""

import time

from google import genai
from google.genai import types

from apps.engine.app.ports.output.embedding_port import EmbeddingPort


class GeminiEmbedding(EmbeddingPort):
    def __init__(self, api_key: str, model: str = "gemini-embedding-001", dimensions: int = 2560) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._dimensions = dimensions  # 128~3072 (기본 3072를 MRL 절단), 로컬 qwen과 같은 값을 쓴다

    def embed(self, texts: list[str], task_type: str | None = None) -> list[list[float]]:
        delay = 1.0
        for attempt in range(4):
            try:
                res = self._client.models.embed_content(
                    model=self._model,
                    contents=texts,
                    config=types.EmbedContentConfig(output_dimensionality=self._dimensions, task_type=task_type),
                )
                return [e.values for e in res.embeddings]
            except Exception as exc:  # 429 포함 일시 오류 — 지수 백오프
                if attempt == 3:
                    raise
                if "429" not in str(exc) and "RESOURCE_EXHAUSTED" not in str(exc):
                    raise
                time.sleep(delay)
                delay *= 2
        raise RuntimeError("unreachable")

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text], task_type="RETRIEVAL_QUERY")[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed(texts, task_type="RETRIEVAL_DOCUMENT")
