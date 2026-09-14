"""Gemini completion adapter; one SDK request behind the existing LLMPort."""

import json
from threading import Lock
from time import monotonic, sleep

from google import genai
from google.genai import types

from apps.engine.app.ports.output.llm_port import LLMParseError, MessageDTO


_request_lock = Lock()
_last_request_at: float | None = None


def _pace_request(requests_per_minute: int) -> None:
    """Share admission spacing across all completion adapters in this process."""
    global _last_request_at
    with _request_lock:
        if _last_request_at is not None:
            delay = _last_request_at + 60.0 / requests_per_minute - monotonic()
            if delay > 0:
                sleep(delay)
        _last_request_at = monotonic()


class GeminiLLM:
    def __init__(self, api_key: str, model: str, timeout: float = 120.0,
                 requests_per_minute: int = 10) -> None:
        if not api_key.strip():
            raise ValueError("Gemini LLM에는 GEMINI_API_KEY 설정이 필요하다")
        if requests_per_minute <= 0:
            raise ValueError("Gemini requests_per_minute must be positive")
        self._requests_per_minute = requests_per_minute
        self._client = genai.Client(
            api_key=api_key, http_options=types.HttpOptions(timeout=int(timeout * 1000)),
        )
        self._model = model

    def complete(
        self, messages: list[MessageDTO], json_schema: dict,
        *, temperature: float | None = None,
    ) -> dict:
        instructions = [m.content for m in messages if m.role == "system"]
        contents = [
            types.Content(role="model" if m.role == "assistant" else "user",
                          parts=[types.Part.from_text(text=m.content)])
            for m in messages if m.role != "system"
        ]
        # Advisor and planner calls can contain only system instructions.
        if not contents:
            contents = [types.Content(role="user", parts=[types.Part.from_text(
                text="위 지시에 따라 JSON으로 응답하라.")])]
        config = types.GenerateContentConfig(
            system_instruction="\n\n".join(instructions) or None,
            temperature=0.7 if temperature is None else temperature,
            response_mime_type="application/json",
            response_json_schema=json_schema or None,
        )
        _pace_request(self._requests_per_minute)
        response = self._client.models.generate_content(
            model=self._model, contents=contents, config=config,
        )
        block_reason = getattr(response.prompt_feedback, "block_reason", None)
        finish_reason = response.candidates[0].finish_reason if response.candidates else None
        if (block_reason not in (None, types.BlockedReason.BLOCKED_REASON_UNSPECIFIED)
                or finish_reason not in (None, types.FinishReason.FINISH_REASON_UNSPECIFIED,
                                         types.FinishReason.STOP, types.FinishReason.MAX_TOKENS)):
            raise RuntimeError(f"Gemini 생성 중단: block_reason={block_reason}, finish_reason={finish_reason}")
        text = response.text
        if not text or not text.strip():
            raise LLMParseError(f"Gemini 응답 text가 비어 있다: finish_reason={finish_reason}")
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMParseError("Gemini 응답이 유효한 JSON이 아니다") from exc
        if not isinstance(parsed, dict):
            raise LLMParseError("Gemini 응답은 JSON object여야 한다")
        return parsed
