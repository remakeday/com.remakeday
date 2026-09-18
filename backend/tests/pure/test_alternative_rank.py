"""직접 쓰기 대안 순위 전략 — 어간 겹침(기본)·임베딩 코사인·폴백 (부록 A.20)."""

from apps.engine.app.ports.output.embedding_port import EmbeddingPort
from apps.engine.app.use_cases.alternative_rank import EmbeddingRank, StemOverlapRank
from apps.engine.app.use_cases.intervention_interactor import suggest_alternatives

TEMPLATES = [
    {"target": "채연", "when_beat": 4, "effect": "enforce", "action": "검진을 받는다", "label": "채연: 검진을 받는다"},
    {"target": "채연", "when_beat": 1, "effect": "enforce", "action": "배급을 남긴다", "label": "채연: 배급을 남긴다"},
    {"target": "채연", "when_beat": 1, "effect": "enforce", "action": "알고 있는 관찰을 설명한다",
     "label": "채연: 알고 있는 관찰을 설명한다"},
]

# 결정론 가짜 임베딩 — 문장·행동을 3차원 축에 손으로 배치한다.
_VECTORS = {
    "밥을 나눠주지 마": [1.0, 0.1, 0.0],
    "배급을 남긴다": [0.9, 0.0, 0.1],
    "검진을 받는다": [0.0, 1.0, 0.0],
    "알고 있는 관찰을 설명한다": [0.0, 0.0, 1.0],
}


class FakeVectors(EmbeddingPort):
    def __init__(self):
        self.calls: list[list[str]] = []

    def embed(self, texts):
        self.calls.append(list(texts))
        return [_VECTORS[t] for t in texts]


class Broken(EmbeddingPort):
    def embed(self, texts):
        raise ConnectionError("ollama down")


ACTIONS = ["검진을 받는다", "배급을 남긴다", "알고 있는 관찰을 설명한다"]


def test_stem_overlap_scores_by_two_char_stem_hits():
    # 어간 "검진"만 "검진을 받는다"에 들어간다("받게"≠"받는")
    scores = StemOverlapRank().rank("채연이 검진을 꼭 받게 해줘", ACTIONS)
    assert scores == [1, 0, 0]


def test_embedding_rank_orders_by_cosine_similarity():
    scores = EmbeddingRank(FakeVectors()).rank("밥을 나눠주지 마", ACTIONS)
    assert sorted(ACTIONS, key=lambda a: -scores[ACTIONS.index(a)]) == ["배급을 남긴다", "검진을 받는다", "알고 있는 관찰을 설명한다"]


def test_embedding_rank_beats_stem_overlap_on_synonyms():
    # 어간 경로는 "밥"·"나눠"로 "배급"을 못 잡고 원래 순서를 유지한다; 임베딩 경로는 배급을 앞세운다.
    text = "밥을 나눠주지 마"
    assert suggest_alternatives(text, ["채연"], TEMPLATES)[0] == "채연은 검진을 받는다"
    assert suggest_alternatives(text, ["채연"], TEMPLATES, rank=EmbeddingRank(FakeVectors()))[0] == "채연은 배급을 남긴다"


def test_embedding_rank_falls_back_to_stem_overlap_on_any_error():
    text = "채연이 검진을 꼭 받게 해줘"
    assert EmbeddingRank(Broken()).rank(text, ACTIONS) == StemOverlapRank().rank(text, ACTIONS)
    assert (suggest_alternatives(text, ["채연"], TEMPLATES, rank=EmbeddingRank(Broken()))
            == suggest_alternatives(text, ["채연"], TEMPLATES))


def test_action_vectors_are_embedded_once_per_process():
    vectors = FakeVectors()
    rank = EmbeddingRank(vectors)
    rank.rank("밥을 나눠주지 마", ACTIONS)
    rank.rank("밥을 나눠주지 마", ACTIONS)
    action_batches = [c for c in vectors.calls if c != ["밥을 나눠주지 마"]]
    assert action_batches == [ACTIONS]
    assert vectors.calls.count(["밥을 나눠주지 마"]) == 2


def test_fallback_logs_one_warning(caplog):
    with caplog.at_level("WARNING"):
        EmbeddingRank(Broken()).rank("밥", ACTIONS)
    assert len([r for r in caplog.records if r.levelname == "WARNING"]) == 1


def test_short_embed_documents_reply_falls_back_instead_of_key_error():
    class Short:
        def embed_documents(self, texts):
            return [[1.0, 0.0]] * (len(texts) - 1)  # 후보보다 하나 적게 — 예외 없이 짧은 응답

        def embed_query(self, text):
            return [1.0, 0.0]

    rank = EmbeddingRank(Short())
    assert rank.rank("채연이 배급 남기게", ["배급을 남긴다", "검진을 받는다", "방송실에 간다"]) == \
        StemOverlapRank().rank("채연이 배급 남기게", ["배급을 남긴다", "검진을 받는다", "방송실에 간다"])
