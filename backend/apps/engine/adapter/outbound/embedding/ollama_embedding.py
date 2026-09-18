"""Ollama 임베딩 어댑터 — /api/embed.

dimensions는 MRL 절단 요청(qwen3-embedding:4b 기본 2560 — Gemini도 2560으로 맞춘다, 사용자 확정 2026-09-18. lifetutorial은 1536).
모델이 그보다 작으면 ollama가 무시하고 고유 차원을 준다(bge-m3 → 1024, 오류 없음). None이면 필드를 보내지 않아 고유 차원 그대로.
응답 벡터는 절단 후에도 L2 정규화돼 있다(2026-09-18 실측 노름 1.000000 — qwen 2560/1536, bge-m3 1024). 코사인은 어차피 노름으로 나눈다.

질의/문서 비대칭: ollama /api/embed는 지시문을 붙이지 않으므로(--template은 chat용) Qwen3-Embedding 형식
`Instruct: {task}\nQuery: {text}`를 질의 쪽에만 붙인다(lifetutorial prompt_name="query"와 같은 역할). 문서(행동 문구)는 그대로.
"""

import httpx

from apps.engine.app.ports.output.embedding_port import EmbeddingPort

RUNTIME_DIM = 2560  # Settings.embedding_dimensions 기본과 같은 값

# Qwen3-Embedding 질의 지시문 — 지시문을 쓰지 않는 모델(bge-m3)은 None으로 끈다.
QWEN3_QUERY_INSTRUCT = "Given a player's rule sentence, retrieve the action phrase it asks for"


class OllamaEmbedding(EmbeddingPort):
    def __init__(self, base_url: str, model: str, timeout: float = 60.0,
                 dimensions: int | None = RUNTIME_DIM,
                 query_instruct: str | None = QWEN3_QUERY_INSTRUCT) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._dimensions = dimensions
        self._query_instruct = query_instruct

    def embed(self, texts: list[str]) -> list[list[float]]:
        body = {"model": self._model, "input": texts, "keep_alive": "2h"}
        if self._dimensions is not None:
            body["dimensions"] = self._dimensions
        res = httpx.post(f"{self._base_url}/api/embed", json=body, timeout=self._timeout)
        res.raise_for_status()
        return res.json()["embeddings"]

    def embed_query(self, text: str) -> list[float]:
        if self._query_instruct is not None:
            text = f"Instruct: {self._query_instruct}\nQuery: {text}"
        return self.embed([text])[0]
