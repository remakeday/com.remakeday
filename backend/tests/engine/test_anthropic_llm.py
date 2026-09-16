"""Anthropic adapter boundary contracts; no network, real credentials."""
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest

from apps.engine.app.ports.output.llm_port import LLMParseError, MessageDTO


def text_block(text):
    return NS(type="text", text=text)


def response(text='{"ok": true}', stop_reason="end_turn"):
    return NS(stop_reason=stop_reason, content=[text_block(text)])


@pytest.fixture
def fake_client():
    create = Mock(return_value=response())
    client = NS(messages=NS(create=create))
    return client, create


def adapter(fake_client, model="claude-sonnet-5", **kwargs):
    from apps.engine.adapter.outbound.llm.anthropic_llm import AnthropicLLM
    client, _ = fake_client
    return AnthropicLLM(api_key="test-key", model=model, client=client, **kwargs)


def sent_kwargs(create):
    return create.call_args.kwargs


def test_system_messages_join_into_top_level_system(fake_client):
    client, create = fake_client
    adapter(fake_client).complete(
        [MessageDTO(role="system", content="규칙 하나"),
         MessageDTO(role="system", content="규칙 둘"),
         MessageDTO(role="user", content="질문")], {})
    kwargs = sent_kwargs(create)
    assert kwargs["system"] == "규칙 하나\n\n규칙 둘"
    assert kwargs["messages"] == [{"role": "user", "content": "질문"}]


def test_system_only_request_appends_user_fallback(fake_client):
    client, create = fake_client
    adapter(fake_client).complete([MessageDTO(role="system", content="지시")], {})
    kwargs = sent_kwargs(create)
    assert kwargs["messages"] == [{"role": "user", "content": "위 지시에 따라 JSON만 출력하라."}]


def test_user_assistant_order_is_preserved(fake_client):
    client, create = fake_client
    adapter(fake_client).complete(
        [MessageDTO(role="user", content="첫 질문"),
         MessageDTO(role="assistant", content="이전 답"),
         MessageDTO(role="user", content="다음 질문")], {})
    assert sent_kwargs(create)["messages"] == [
        {"role": "user", "content": "첫 질문"},
        {"role": "assistant", "content": "이전 답"},
        {"role": "user", "content": "다음 질문"},
    ]


def test_effort_present_for_non_haiku_model(fake_client):
    client, create = fake_client
    adapter(fake_client, model="claude-sonnet-5", effort="high").complete(
        [MessageDTO(role="user", content="질문")], {})
    assert sent_kwargs(create)["output_config"]["effort"] == "high"


def test_effort_absent_for_haiku_model(fake_client):
    client, create = fake_client
    adapter(fake_client, model="claude-haiku-4-5", effort="high").complete(
        [MessageDTO(role="user", content="질문")], {"type": "object"})
    output_config = sent_kwargs(create)["output_config"]
    assert "effort" not in output_config
    assert output_config["format"] == {"type": "json_schema", "schema": {"type": "object"}}


def test_json_schema_omitted_when_empty(fake_client):
    client, create = fake_client
    adapter(fake_client).complete([MessageDTO(role="user", content="질문")], {})
    assert "format" not in sent_kwargs(create).get("output_config", {})


def test_temperature_is_never_sent(fake_client):
    client, create = fake_client
    adapter(fake_client).complete([MessageDTO(role="user", content="질문")], {}, temperature=0.5)
    assert "temperature" not in sent_kwargs(create)


def test_json_text_parses_to_dict(fake_client):
    client, create = fake_client
    create.return_value = response('{"ok": true}')
    assert adapter(fake_client).complete([MessageDTO(role="user", content="질문")], {}) == {"ok": True}


def test_invalid_json_raises_parse_error(fake_client):
    client, create = fake_client
    create.return_value = response("not json")
    with pytest.raises(LLMParseError):
        adapter(fake_client).complete([MessageDTO(role="user", content="질문")], {})


def test_refusal_stop_reason_raises_parse_error(fake_client):
    client, create = fake_client
    create.return_value = response("", stop_reason="refusal")
    with pytest.raises(LLMParseError):
        adapter(fake_client).complete([MessageDTO(role="user", content="질문")], {})


def test_missing_api_key_fails_before_client_is_created():
    from apps.engine.adapter.outbound.llm.anthropic_llm import AnthropicLLM
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        AnthropicLLM(api_key="", model="claude-sonnet-5")


def test_factory_selects_anthropic_and_raises_when_key_blank(monkeypatch):
    from apps.engine.dependencies import llm_factory as factory
    from apps.engine.adapter.outbound.llm.anthropic_llm import AnthropicLLM

    monkeypatch.setattr(factory, "get_settings",
                        lambda: NS(anthropic_api_key="test-key", anthropic_effort="low"))
    llm = factory.build_llm("anthropic", "claude-sonnet-5", "", "default")
    assert isinstance(llm, AnthropicLLM) and llm._model == "claude-sonnet-5"

    monkeypatch.setattr(factory, "get_settings",
                        lambda: NS(anthropic_api_key="", anthropic_effort="low"))
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        factory.build_llm("anthropic", "claude-sonnet-5", "", "default")
