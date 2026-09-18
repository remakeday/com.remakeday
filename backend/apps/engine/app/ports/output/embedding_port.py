from typing import Protocol

# 차원이 같아도 공간이 다르다 — provider별 벡터는 한 컬럼에 섞지 않는다(lifetutorial 방식: embedding/embedding_local 컬럼 분리).
# 여기서는 테이블을 쓰지 않으므로 컬럼은 없고, 비교는 벡터가 아니라 순위 일치도로만 한다.
EMBEDDING_DIM = 1536  # 미사용 pgvector 컬럼(truth_claim_embeddings) 규격 — 런타임 차원은 Settings.embedding_dimensions(2560)


class EmbeddingPort(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    # 질의/문서 비대칭(lifetutorial EmbeddingPort와 같은 형태) — 기본 구현은 embed()를 부른다.
    # 어댑터가 명시적으로 이 클래스를 상속해야 기본 구현을 물려받는다.
    def embed_query(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed(texts)
