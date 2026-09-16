"""Anthropic 어댑터 — Messages API, structured output(output_config.format).

JSON 파싱 실패는 LLMParseError(하네스 재생성). refusal·max_tokens 절단 등 재시도해도
같은 결과인 stop_reason은 LLMRefusalError(하네스가 재생성 없이 즉시 폴백).
"""

import copy
import json

import anthropic

from apps.engine.app.ports.output.llm_port import LLMParseError, LLMRefusalError, MessageDTO

_USER_FALLBACK = "위 지시에 따라 JSON만 출력하라."

# Anthropic structured outputs(messages.create + output_config.format)는 이 키들을
# 지원하지 않는다 — 숫자/문자열/배열 제약 (shared/tool-use-concepts.md § JSON Schema
# Limitations). .parse()만 클라이언트 측에서 이를 제거하므로 create()를 쓰는 우리는 직접 벗긴다.
_UNSUPPORTED_SCHEMA_KEYWORDS = frozenset({
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "minLength", "maxLength", "minItems", "maxItems", "multipleOf",
})

# 재시도해도 같은 응답이 나오는 stop_reason — 하네스 재생성 대상이 아니다.
# model_context_window_exceeded는 현재 문서화된 값이 아니다 — 향후 나올 수 있는
# stop_reason에 대한 대비이며, 실제로 나오지 않아도 무해하다.
_NON_RETRYABLE_STOP_REASONS = frozenset({
    "refusal", "max_tokens", "model_context_window_exceeded",
})


def strip_unsupported_schema_keywords(schema: dict) -> dict:
    """Anthropic이 거부하는 JSON Schema 제약 키를 재귀적으로 제거한 복사본을 반환한다.

    minItems는 0/1일 때는 SDK와 동일하게 유지한다. 그 외에 제거되는 키는 값을 잃지 않도록
    같은 노드의 description에 제약을 이어 붙인다(모델이 여전히 제약을 볼 수 있도록).
    """

    def _strip(node):
        if isinstance(node, dict):
            stripped = {}
            notes = []
            for key, value in node.items():
                if key in _UNSUPPORTED_SCHEMA_KEYWORDS:
                    if key == "minItems" and value in (0, 1):
                        stripped[key] = value
                    else:
                        notes.append(f"{key}={value}")
                    continue
                stripped[key] = _strip(value)
            if notes:
                note = f"(제약: {', '.join(notes)})"
                stripped["description"] = f"{stripped.get('description', '')} {note}".strip()
            return stripped
        if isinstance(node, list):
            return [_strip(item) for item in node]
        return node

    return _strip(copy.deepcopy(schema))


class AnthropicLLM:
    def __init__(self, api_key: str, model: str, timeout: float = 120.0,
                 effort: str = "low", max_tokens: int = 4096, client=None) -> None:
        if not api_key.strip():
            raise ValueError("Anthropic LLM에는 ANTHROPIC_API_KEY 설정이 필요하다")
        self._model = model
        self._effort = effort
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._client = client if client is not None else anthropic.Anthropic(
            api_key=api_key, timeout=timeout)

    def complete(
        self, messages: list[MessageDTO], json_schema: dict,
        *, temperature: float | None = None,
    ) -> dict:
        # Claude Opus 5 / Sonnet 5는 temperature 파라미터가 제거되어 400을 내므로 하이쿠에만 보낸다.
        is_haiku = self._model.startswith("claude-haiku")
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        turns = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        if not turns:
            turns.append({"role": "user", "content": _USER_FALLBACK})

        output_config = {}
        if json_schema:
            output_config["format"] = {
                "type": "json_schema",
                "schema": strip_unsupported_schema_keywords(json_schema),
            }
        if not is_haiku:
            output_config["effort"] = self._effort

        kwargs = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": turns,
        }
        if system:
            kwargs["system"] = system
        if output_config:
            kwargs["output_config"] = output_config
        # thinking 파라미터는 보내지 않는다 — Opus 5류에서 disabled는 두 가지 실패 모드가
        # 있다(도구 호출이 visible text로 새거나 <thinking> 태그 누출); adaptive 기본을 그대로
        # 두고 output_config.effort로만 깊이를 제어한다.
        # SDK 1.6부터 messages.create()에 top-level temperature 인자가 없다(TypeError) —
        # API는 하이쿠에 한해 여전히 temperature를 받으므로 extra_body로 우회해 전달한다.
        if is_haiku and temperature is not None:
            kwargs["extra_body"] = {"temperature": temperature}

        response = self._client.messages.create(**kwargs)

        if response.stop_reason in _NON_RETRYABLE_STOP_REASONS:
            raise LLMRefusalError(f"Anthropic 응답이 {response.stop_reason}로 종료됨")

        text = "".join(block.text for block in response.content if block.type == "text")
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMParseError(f"JSON 파싱 실패: {text[:200]}") from exc
