"""Gemini SDK boundary contracts; no network, real credentials or database."""
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest
from google import genai
from google.genai import errors, types

from apps.engine.app.dtos.llm_output_dto import AdvisorEvidenceOutput
from apps.engine.app.ports.output.llm_port import LLMParseError, MessageDTO
from apps.engine.app.use_cases.harness import run_with_harness


def response(text='{"evidence": []}', finish="STOP"):
    return types.GenerateContentResponse(candidates=[types.Candidate(
        content=types.Content(role="model", parts=[types.Part.from_text(text=text)]), finish_reason=finish)])


@pytest.fixture
def sdk(monkeypatch):
    from apps.engine.adapter.outbound.llm import gemini_llm
    monkeypatch.setattr(gemini_llm, "_pace_request", lambda _: None)
    generate = Mock(return_value=response())
    constructor = Mock(return_value=NS(models=NS(generate_content=generate)))
    monkeypatch.setattr(genai, "Client", constructor)
    return NS(constructor=constructor, generate=generate)


def adapter():
    from apps.engine.adapter.outbound.llm.gemini_llm import GeminiLLM
    return GeminiLLM(api_key="test-key", model="gemini-test")


@pytest.mark.parametrize(("temperature", "expected"), [(0, 0), (0.4, 0.4), (None, 0.7)])
def test_message_roles_nested_schema_and_temperature_are_preserved(sdk, temperature, expected):
    llm = adapter()
    messages = [MessageDTO(role="system", content="규칙 하나"), MessageDTO(role="system", content="규칙 둘"),
                MessageDTO(role="user", content="첫 질문"), MessageDTO(role="assistant", content="이전 답"),
                MessageDTO(role="user", content="다음 질문")]
    schema = AdvisorEvidenceOutput.model_json_schema()
    assert llm.complete(messages, schema, temperature=temperature) == {"evidence": []}
    call = sdk.generate.call_args.kwargs
    assert call["model"] == "gemini-test"
    assert [(c.role, c.parts[0].text) for c in call["contents"]] == [("user", "첫 질문"), ("model", "이전 답"), ("user", "다음 질문")]
    config = call["config"]
    assert config.system_instruction == "규칙 하나\n\n규칙 둘"
    assert config.response_mime_type == "application/json"
    assert config.response_json_schema == schema and config.response_schema is None
    assert config.temperature == expected
    assert sdk.constructor.call_args.kwargs["http_options"].timeout == 120000
    assert sdk.generate.call_count == 1


def test_system_only_advisor_request_keeps_instruction_and_nonempty_user_trigger(sdk):
    adapter().complete([MessageDTO(role="system", content="공개 기록만 판단한다")], {"type": "object"})
    call = sdk.generate.call_args.kwargs
    assert call["config"].system_instruction == "공개 기록만 판단한다"
    assert len(call["contents"]) == 1 and call["contents"][0].role == "user"
    assert call["contents"][0].parts[0].text.strip()


@pytest.mark.parametrize("text", ["", " ", "not JSON", "[]", "null", "42", '"text"'])
def test_empty_malformed_and_nonobject_response_is_parse_failure(sdk, text):
    sdk.generate.return_value = response(text)
    with pytest.raises(LLMParseError):
        adapter().complete([MessageDTO(role="user", content="질문")], {})
    assert sdk.generate.call_count == 1


def test_missing_text_records_finish_reason_in_parse_failure(sdk):
    sdk.generate.return_value = types.GenerateContentResponse(candidates=[types.Candidate(finish_reason="MAX_TOKENS")])
    with pytest.raises(LLMParseError, match="MAX_TOKENS"):
        adapter().complete([], {})


@pytest.mark.parametrize("where", ["prompt", "candidate"])
def test_blocked_response_is_provider_failure_with_reason(sdk, where):
    sdk.generate.return_value = (types.GenerateContentResponse(prompt_feedback=types.GenerateContentResponsePromptFeedback(block_reason="SAFETY"))
                                if where == "prompt" else response("", finish="SAFETY"))
    with pytest.raises(RuntimeError, match="SAFETY"):
        adapter().complete([], {})
    assert sdk.generate.call_count == 1


@pytest.mark.parametrize("key", ["", "   "])
def test_missing_key_fails_before_sdk_client_is_created(sdk, key):
    from apps.engine.adapter.outbound.llm.gemini_llm import GeminiLLM
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiLLM(api_key=key, model="gemini-test")
    sdk.constructor.assert_not_called()


def test_sdk_exception_is_preserved_and_harness_logs_one_provider_call(sdk):
    error = errors.ClientError(429, {"error": {"message": "test quota", "status": "RESOURCE_EXHAUSTED"}})
    sdk.generate.side_effect = error
    llm = adapter()
    with pytest.raises(errors.ClientError) as caught:
        llm.complete([], {})
    assert caught.value is error
    sdk.generate.reset_mock()
    result, report = run_with_harness(llm, [MessageDTO(role="system", content="판단")], AdvisorEvidenceOutput, role="advisor_answer", temperature=0)
    assert result is None and report.fallback_used and report.attempts == 1
    assert report.model == "gemini-test" and "ClientError" in report.call_records[0]["error"]
    assert sdk.generate.call_count == 1


def test_factory_selects_gemini_and_role_settings_remain_independent(sdk, monkeypatch):
    from apps.engine.dependencies import llm_factory as factory
    from apps.engine.adapter.outbound.llm.gemini_llm import GeminiLLM
    from apps.engine.adapter.outbound.llm.ollama_llm import OllamaLLM
    settings = NS(core_llm_provider="gemini", core_llm_model="gemini-test", gemini_api_key="test-key",
                  npc_llm_provider="ollama", npc_llm_model="local-test-model", ollama_base_url="http://local.invalid", gemini_requests_per_minute=10)
    monkeypatch.setattr(factory, "get_settings", lambda: settings)
    factory.get_core_llm.cache_clear(); factory.get_npc_llm.cache_clear()
    try:
        core, npc = factory.get_core_llm(), factory.get_npc_llm()
        assert isinstance(core, GeminiLLM) and core._model == "gemini-test"
        assert isinstance(npc, OllamaLLM) and npc._model == "local-test-model"
        assert npc._base_url == "http://local.invalid"
        assert sdk.constructor.call_args.kwargs["api_key"] == "test-key"
    finally:
        factory.get_core_llm.cache_clear(); factory.get_npc_llm.cache_clear()
