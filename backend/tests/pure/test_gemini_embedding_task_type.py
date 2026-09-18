"""Gemini 임베딩 어댑터 — 질의/문서 task_type 비대칭; no network."""
from types import SimpleNamespace as NS

import pytest


@pytest.fixture
def adapter(monkeypatch):
    from google import genai

    from apps.engine.adapter.outbound.embedding.gemini_embedding import GeminiEmbedding
    monkeypatch.setattr(genai, "Client", lambda **_: NS())
    emb = GeminiEmbedding(api_key="test")
    emb.calls = []

    def embed_content(*, model, contents, config):
        emb.calls.append((contents, config.task_type, config.output_dimensionality))
        return NS(embeddings=[NS(values=[0.1]) for _ in contents])

    emb._client = NS(models=NS(embed_content=embed_content))
    return emb


def test_query_and_documents_use_retrieval_task_types(adapter):
    assert adapter.embed_query("밥") == [0.1]
    assert adapter.embed_documents(["가", "나"]) == [[0.1], [0.1]]
    assert adapter.embed(["다"]) == [[0.1]]
    assert adapter.calls == [(["밥"], "RETRIEVAL_QUERY", 2560), (["가", "나"], "RETRIEVAL_DOCUMENT", 2560),
                             (["다"], None, 2560)]
