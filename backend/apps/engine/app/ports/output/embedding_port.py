from typing import Protocol

EMBEDDING_DIM = 1536


class EmbeddingPort(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
