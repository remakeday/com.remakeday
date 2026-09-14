"""Gemini 임베딩 어댑터 — 1,536차원, 429 지수 백오프."""

import time

from google import genai
from google.genai import types

from apps.engine.app.ports.output.embedding_port import EMBEDDING_DIM


class GeminiEmbedding:
    def __init__(self, api_key: str, model: str = "gemini-embedding-001") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        delay = 1.0
        for attempt in range(4):
            try:
                res = self._client.models.embed_content(
                    model=self._model,
                    contents=texts,
                    config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
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
