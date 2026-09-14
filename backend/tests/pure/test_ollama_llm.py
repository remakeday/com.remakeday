"""Ollama adapter boundary contracts — think 제어; no network."""
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest

from apps.engine.app.ports.output.llm_port import MessageDTO


def response(content='{"reply": "응"}'):
    return NS(raise_for_status=lambda: None,
              json=lambda: {"message": {"content": content}})


@pytest.fixture
def post(monkeypatch):
    from apps.engine.adapter.outbound.llm import ollama_llm
    mock = Mock(return_value=response())
    monkeypatch.setattr(ollama_llm.httpx, "post", mock)
    return mock


def adapter(**kwargs):
    from apps.engine.adapter.outbound.llm.ollama_llm import OllamaLLM
    return OllamaLLM(base_url="http://local.invalid", model="test-model", **kwargs)


def sent_body(post):
    return post.call_args.kwargs["json"]


def test_default_omits_think_field_for_backward_compatibility(post):
    adapter().complete([MessageDTO(role="user", content="질문")], {})
    assert "think" not in sent_body(post)


@pytest.mark.parametrize("think", [False, True])
def test_explicit_think_is_sent_verbatim(post, think):
    adapter(think=think).complete([MessageDTO(role="user", content="질문")], {})
    assert sent_body(post)["think"] is think


def test_think_does_not_alter_existing_body_contract(post):
    schema = {"type": "object"}
    adapter(think=False).complete(
        [MessageDTO(role="system", content="규칙"), MessageDTO(role="user", content="질문")],
        schema, temperature=0.2)
    body = sent_body(post)
    assert body["model"] == "test-model" and body["format"] == schema
    assert body["options"]["temperature"] == 0.2 and body["keep_alive"] == "2h"
    assert body["messages"][0] == {"role": "system", "content": "규칙"}


def _settings(**over):
    base = dict(core_llm_provider="ollama", core_llm_model="core-m", core_llm_think="off",
                npc_llm_provider="ollama", npc_llm_model="npc-m", npc_llm_think="default",
                ollama_base_url="http://local.invalid",
                gemini_api_key="", gemini_requests_per_minute=10)
    base.update(over)
    return NS(**base)


@pytest.fixture
def factory(monkeypatch):
    from apps.engine.dependencies import llm_factory as f
    f.get_core_llm.cache_clear(); f.get_npc_llm.cache_clear()
    yield f
    f.get_core_llm.cache_clear(); f.get_npc_llm.cache_clear()


def test_factory_wires_think_off_to_core_and_default_to_npc(factory, monkeypatch):
    monkeypatch.setattr(factory, "get_settings", _settings)
    core, npc = factory.get_core_llm(), factory.get_npc_llm()
    assert core._think is False
    assert npc._think is None


def test_factory_wires_think_on(factory, monkeypatch):
    monkeypatch.setattr(factory, "get_settings", lambda: _settings(npc_llm_think="on"))
    assert factory.get_npc_llm()._think is True


def test_factory_rejects_unknown_think_value_fail_fast(factory, monkeypatch):
    monkeypatch.setattr(factory, "get_settings", lambda: _settings(core_llm_think="never"))
    with pytest.raises(ValueError, match="think"):
        factory.get_core_llm()
