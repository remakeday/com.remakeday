"""직접 쓰기 대안 순위 전략 (Strategy) — 어간 겹침(기본)·임베딩 코사인.

임베딩이 되살아난 유일한 자리다(부록 A.20): 플레이어가 고르는 추천이라 틀려도 게이트에 무해하다.
채점·NPC 기억·단서 해금에는 쓰지 않는다.
"""

import logging
import math
import re
from typing import Protocol

from apps.engine.app.ports.output.embedding_port import EmbeddingPort

logger = logging.getLogger(__name__)

_HANGUL_TOKEN_RE = re.compile(r"[가-힣]{2,}")


class AlternativeRank(Protocol):
    def rank(self, text: str, candidates: list[str]) -> list[float]:
        """후보(행동 문구)마다 문장과의 근접도 — 클수록 가깝다. 후보 순서 그대로 돌려준다."""
        ...


class StemOverlapRank:
    """근접도 = 문장의 한글 토큰 어간(앞 2글자)이 행동 문구에 들어 있는 개수."""

    def rank(self, text: str, candidates: list[str]) -> list[float]:
        stems = {token[:2] for token in _HANGUL_TOKEN_RE.findall(text)}
        return [sum(stem in candidate for stem in stems) for candidate in candidates]


class EmbeddingRank:
    """근접도 = 코사인 유사도. embed()가 어떤 예외를 내든 어간 겹침으로 폴백한다 — 임베딩이 죽어도 게임은 멈추지 않는다.

    행동 문구는 시나리오당 상수라 프로세스 안에서 한 번만 임베딩한다(문구별 캐시). 플레이어 문장은 매번.
    플레이어 문장 = query, 행동 문구 = document(어댑터가 지시문·task_type으로 비대칭을 건다).
    """

    def __init__(self, embedding: EmbeddingPort) -> None:
        self._embedding = embedding
        self._fallback = StemOverlapRank()
        self._vectors: dict[str, list[float]] = {}

    def rank(self, text: str, candidates: list[str]) -> list[float]:
        try:
            missing = [c for c in dict.fromkeys(candidates) if c not in self._vectors]
            if missing:
                self._vectors.update(zip(missing, self._embedding.embed_documents(missing)))
            query = self._embedding.embed_query(text)
            # 캐시 조회도 try 안 — embed_documents가 후보 수보다 짧게 돌려주면 KeyError도 폴백으로 간다.
            return [_cosine(query, self._vectors[c]) for c in candidates]
        except Exception as exc:  # noqa: BLE001 — 폴백이 전제다
            logger.warning("임베딩 실패, 어간 겹침으로 폴백: %s", exc)
            return self._fallback.rank(text, candidates)


def _cosine(a: list[float], b: list[float]) -> float:
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b)) / norm if norm else 0.0
