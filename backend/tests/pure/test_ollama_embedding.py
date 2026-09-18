"""Ollama 임베딩 어댑터 경계 — /api/embed 요청 본문·dimensions; no network."""
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest


@pytest.fixture
def post(monkeypatch):
    from apps.engine.adapter.outbound.embedding import ollama_embedding
    mock = Mock(return_value=NS(raise_for_status=lambda: None,
                                json=lambda: {"embeddings": [[0.1, 0.2], [0.3, 0.4]]}))
    monkeypatch.setattr(ollama_embedding.httpx, "post", mock)
    return mock


def adapter(**kwargs):
    from apps.engine.adapter.outbound.embedding.ollama_embedding import OllamaEmbedding
    return OllamaEmbedding(base_url="http://local.invalid/", model="emb-test", **kwargs)


def test_posts_to_api_embed_with_default_2560_dimensions(post):
    assert adapter().embed(["가", "나"]) == [[0.1, 0.2], [0.3, 0.4]]
    assert post.call_args.args[0] == "http://local.invalid/api/embed"
    body = post.call_args.kwargs["json"]
    assert body["model"] == "emb-test" and body["input"] == ["가", "나"] and body["dimensions"] == 2560


def test_dimensions_none_leaves_model_native(post):
    adapter(dimensions=None).embed(["가"])
    assert "dimensions" not in post.call_args.kwargs["json"]


def test_query_gets_qwen3_instruct_prefix_and_documents_do_not(post):
    a = adapter()
    a.embed_query("밥 나눠주지 마")
    sent = post.call_args.kwargs["json"]["input"]
    assert sent == ["Instruct: Given a player's rule sentence, retrieve the action phrase it asks for\nQuery: 밥 나눠주지 마"]
    a.embed_documents(["배급을 남긴다"])
    assert post.call_args.kwargs["json"]["input"] == ["배급을 남긴다"]


def test_query_instruct_none_sends_text_verbatim(post):
    adapter(query_instruct=None).embed_query("밥")
    assert post.call_args.kwargs["json"]["input"] == ["밥"]
