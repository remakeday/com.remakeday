"""Ollama 어댑터 — /api/chat, structured output(format=json schema).

JSON 파싱 실패는 LLMParseError로 — 하네스가 재생성으로 처리한다.
"""

import json

import httpx

from apps.engine.app.ports.output.llm_port import LLMParseError, MessageDTO


class OllamaLLM:
    def __init__(self, base_url: str, model: str, timeout: float = 120.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def complete(
        self, messages: list[MessageDTO], json_schema: dict,
        *, temperature: float | None = None,
    ) -> dict:
        body = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "keep_alive": "2h",  # 데모 중 언로드→재로드(30s+) 방지
            "options": {"temperature": 0.7 if temperature is None else temperature},
        }
        if json_schema:
            body["format"] = json_schema
        res = httpx.post(f"{self._base_url}/api/chat", json=body, timeout=self._timeout)
        res.raise_for_status()
        content = res.json()["message"]["content"]
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMParseError(f"JSON 파싱 실패: {content[:200]}") from exc
