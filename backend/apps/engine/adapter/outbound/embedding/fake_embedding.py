"""FakeEmbedding — 결정론 벡터. 같은 입력이면 항상 같은 1,536차원 벡터."""

import hashlib

from apps.engine.app.ports.output.embedding_port import EMBEDDING_DIM, EmbeddingPort


class FakeEmbedding(EmbeddingPort):
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    @staticmethod
    def _vector(text: str) -> list[float]:
        out: list[float] = []
        counter = 0
        while len(out) < EMBEDDING_DIM:
            digest = hashlib.sha256(f"{counter}:{text}".encode()).digest()
            out.extend(b / 255.0 for b in digest)
            counter += 1
        return out[:EMBEDDING_DIM]
