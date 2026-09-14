"""NPC 의심·신뢰 — 계산은 코드. LLM 제안값(delta)을 여기서 최종 확정한다."""

from dataclasses import dataclass, replace

from apps.engine.domain.value_objects.game_constants import (
    DELTA_CAP,
    NPC_MEMORY_TURNS,
    SUSPICION_THRESHOLD,
    TRUST_GAIN_CAP,
    TRUST_RETENTION,
)


@dataclass(frozen=True)
class NpcGauge:
    suspicion: int
    trust: int
    opposite_mode: bool


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def apply_deltas(g: NpcGauge, suspicion_delta: int, trust_delta: int) -> NpcGauge:
    """LLM 제안값 → 최종값. 클램프 + 신뢰 상승 상한 + 임계 판정.

    신뢰는 비용 행동에서만 쌓인다 — 발화는 예산을 소모하므로 비용 행동이되,
    1회 상승은 TRUST_GAIN_CAP으로 제한한다 (말 한 번으로 크게 오르지 않는다).
    """
    sd = _clamp(suspicion_delta, -DELTA_CAP, DELTA_CAP)
    td = _clamp(trust_delta, -DELTA_CAP, TRUST_GAIN_CAP)
    suspicion = _clamp(g.suspicion + sd, 0, 100)
    trust = _clamp(g.trust + td, 0, 100)
    return NpcGauge(
        suspicion=suspicion,
        trust=trust,
        opposite_mode=g.opposite_mode or suspicion >= SUSPICION_THRESHOLD,
    )


def apply_event_suspicion(g: NpcGauge, amount: int) -> NpcGauge:
    """코드가 정한 사건 페널티 (도구 불일치 등) — LLM 제안 클램프를 거치지 않는다."""
    suspicion = _clamp(g.suspicion + amount, 0, 100)
    return NpcGauge(
        suspicion=suspicion,
        trust=g.trust,
        opposite_mode=g.opposite_mode or suspicion >= SUSPICION_THRESHOLD,
    )


def carry_over(g: NpcGauge) -> NpcGauge:
    """회차 리셋 — 의심 소거, 신뢰 5% 잔류, 반대 행동 해제."""
    return NpcGauge(
        suspicion=0, trust=round(g.trust * TRUST_RETENTION), opposite_mode=False
    )


@dataclass(frozen=True)
class NpcMemory:
    turns: tuple[str, ...] = ()


def remember(m: NpcMemory, line: str) -> NpcMemory:
    """최근 3턴만 남긴다 — 망각의 구현."""
    return replace(m, turns=(m.turns + (line,))[-NPC_MEMORY_TURNS:])
