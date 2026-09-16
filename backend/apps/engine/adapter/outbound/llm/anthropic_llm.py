"""Anthropic 어댑터 — Messages API, structured output(output_config.format).

JSON 파싱 실패·refusal·max_tokens 절단은 LLMParseError로 — 하네스가 재생성으로 처리한다.
"""

import copy
import json

import anthropic

from apps.engine.app.ports.output.llm_port import LLMParseError, MessageDTO

_USER_FALLBACK = "위 지시에 따라 JSON만 출력하라."

# Anthropic structured outputs(messages.create + output_config.format)는 이 키들을
# 지원하지 않는다 — 숫자/문자열/배열 제약 (shared/tool-use-concepts.md § JSON Schema
# Limitations). .parse()만 클라이언트 측에서 이를 제거하므로 create()를 쓰는 우리는 직접 벗긴다.
_UNSUPPORTED_SCHEMA_KEYWORDS = frozenset({
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "minLength", "maxLength", "minItems", "maxItems",
})


def strip_unsupported_schema_keywords(schema: dict) -> dict:
    """Anthropic이 거부하는 JSON Schema 제약 키를 재귀적으로 제거한 복사본을 반환한다."""

    def _strip(node):
        if isinstance(node, dict):
            return {
                key: _strip(value)
                for key, value in node.items()
                if key not in _UNSUPPORTED_SCHEMA_KEYWORDS
            }
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
        self._client = client if client is not None else anthropic.Anthropic(
            api_key=api_key, timeout=timeout)

    def complete(
        self, messages: list[MessageDTO], json_schema: dict,
        *, temperature: float | None = None,
    ) -> dict:
        # Claude Opus 5 / Sonnet 5는 temperature 파라미터가 제거되어 400을 내므로 보내지 않는다.
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
        if not self._model.startswith("claude-haiku"):
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

        response = self._client.messages.create(**kwargs)

        if response.stop_reason == "refusal":
            raise LLMParseError("Anthropic 응답이 refusal로 종료됨")
        if response.stop_reason == "max_tokens":
            raise LLMParseError("Anthropic 응답이 max_tokens로 절단됨")

        text = "".join(block.text for block in response.content if block.type == "text")
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMParseError(f"JSON 파싱 실패: {text[:200]}") from exc
