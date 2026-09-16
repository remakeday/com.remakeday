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


def test_max_tokens_stop_reason_raises_parse_error(fake_client):
    client, create = fake_client
    create.return_value = response('{"ok": tr', stop_reason="max_tokens")
    with pytest.raises(LLMParseError, match="max_tokens"):
        adapter(fake_client).complete([MessageDTO(role="user", content="질문")], {})


def test_consecutive_user_messages_are_passed_through_in_order(fake_client):
    client, create = fake_client
    adapter(fake_client).complete(
        [MessageDTO(role="system", content="지시"),
         MessageDTO(role="user", content="원래 답"),
         MessageDTO(role="user", content="틀렸다. 다시 답해라")], {})
    assert sent_kwargs(create)["messages"] == [
        {"role": "user", "content": "원래 답"},
        {"role": "user", "content": "틀렸다. 다시 답해라"},
    ]


def test_missing_api_key_fails_before_client_is_created():
    from apps.engine.adapter.outbound.llm.anthropic_llm import AnthropicLLM
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        AnthropicLLM(api_key="", model="claude-sonnet-5")


def test_factory_selects_anthropic_and_raises_when_key_blank(monkeypatch):
    from apps.engine.dependencies import llm_factory as factory
    from apps.engine.adapter.outbound.llm.anthropic_llm import AnthropicLLM

    monkeypatch.setattr(factory, "get_settings", lambda: NS(
        anthropic_api_key="test-key", anthropic_effort="low", anthropic_max_tokens=8192))
    llm = factory.build_llm("anthropic", "claude-sonnet-5", "", "default")
    assert isinstance(llm, AnthropicLLM) and llm._model == "claude-sonnet-5"

    monkeypatch.setattr(factory, "get_settings", lambda: NS(
        anthropic_api_key="", anthropic_effort="low", anthropic_max_tokens=8192))
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        factory.build_llm("anthropic", "claude-sonnet-5", "", "default")


def test_factory_wires_anthropic_max_tokens_from_settings(monkeypatch):
    from apps.engine.dependencies import llm_factory as factory

    monkeypatch.setattr(factory, "get_settings", lambda: NS(
        anthropic_api_key="test-key", anthropic_effort="low", anthropic_max_tokens=1234))
    llm = factory.build_llm("anthropic", "claude-sonnet-5", "", "default")
    assert llm._max_tokens == 1234


class TestStripUnsupportedSchemaKeywords:
    def test_removes_unsupported_keys_at_every_nesting_level_keeps_supported(self):
        from apps.engine.adapter.outbound.llm.anthropic_llm import strip_unsupported_schema_keywords

        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "minimum": 1, "maximum": 6},
                "name": {"type": "string", "minLength": 1, "maxLength": 20, "enum": ["a", "b"]},
                "items": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "properties": {
                            "n": {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 10},
                        },
                        "required": ["n"],
                        "additionalProperties": False,
                    },
                },
                "nested": {"anyOf": [
                    {"type": "string", "minLength": 1},
                    {"type": "null"},
                ]},
            },
            "$defs": {
                "Sub": {"type": "object", "properties": {"x": {"type": "integer", "minimum": 0}},
                        "required": ["x"], "additionalProperties": False},
            },
            "required": ["count", "name"],
            "additionalProperties": False,
        }

        stripped = strip_unsupported_schema_keywords(schema)

        def collect_keys(node, found):
            if isinstance(node, dict):
                found.update(node.keys())
                for value in node.values():
                    collect_keys(value, found)
            elif isinstance(node, list):
                for item in node:
                    collect_keys(item, found)

        found_keys = set()
        collect_keys(stripped, found_keys)
        assert found_keys.isdisjoint({
            "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
            "minLength", "maxLength", "minItems", "maxItems",
        })
        assert stripped["required"] == ["count", "name"]
        assert stripped["additionalProperties"] is False
        assert stripped["properties"]["name"]["enum"] == ["a", "b"]
        assert stripped["$defs"]["Sub"]["required"] == ["x"]
        # 원본 스키마는 변형되지 않아야 한다(순수 함수 — 딥카피).
        assert schema["properties"]["count"]["minimum"] == 1

    def test_npc_plan_schema_has_no_unsupported_keys_anywhere(self):
        from apps.engine.adapter.outbound.llm.anthropic_llm import strip_unsupported_schema_keywords
        from apps.engine.app.dtos.llm_output_dto import NpcPlan

        raw_schema = NpcPlan.model_json_schema()
        # 벗기기 전엔 실제로 존재해야 이 테스트가 의미 있다(회귀 방지).
        assert "minimum" in str(raw_schema) or "minItems" in str(raw_schema)

        stripped = strip_unsupported_schema_keywords(raw_schema)

        def collect_keys(node, found):
            if isinstance(node, dict):
                found.update(node.keys())
                for value in node.values():
                    collect_keys(value, found)
            elif isinstance(node, list):
                for item in node:
                    collect_keys(item, found)

        found_keys = set()
        collect_keys(stripped, found_keys)
        assert found_keys.isdisjoint({
            "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
            "minLength", "maxLength", "minItems", "maxItems",
        })
