"""StaticScenario — ScenarioBundleDTO 하나를 그대로 서빙하는 ScenarioPort 구현 베이스.

시나리오 고유 명사는 이 파일에 없다. 값은 각 시나리오 어댑터의 번들에만 있다.
"""

from apps.engine.app.dtos.scenario_dto import (
    BeatDTO,
    CharacterDTO,
    CookieTextDTO,
    FragmentDTO,
    ScenarioBundleDTO,
    TruthClaimDTO,
    UtteranceBanDTO,
)


class StaticScenario:
    """정적 번들 기반 ScenarioPort 구현체.

    ScenarioBundleDTO 하나를 받아 모든 포트 메서드를 그 번들에서 읽어 답한다.
    """

    def __init__(self, bundle: ScenarioBundleDTO) -> None:
        self._bundle = bundle

    def name(self) -> str:
        return self._bundle.name

    def bundle(self) -> ScenarioBundleDTO:
        return self._bundle

    def surface_summary(self) -> str:
        return self._bundle.surface_summary

    def hidden_truth(self) -> str:
        return self._bundle.hidden_truth

    def characters(self) -> list[CharacterDTO]:
        return list(self._bundle.characters)

    def beats(self) -> list[BeatDTO]:
        return list(self._bundle.beats)

    def truth_claims(self) -> list[TruthClaimDTO]:
        return list(self._bundle.truth_claims)

    def cookie_texts(self) -> list[CookieTextDTO]:
        return list(self._bundle.cookies)

    def forbidden_words(self) -> list[str]:
        return list(self._bundle.forbidden_words)

    def utterance_bans(self) -> list[UtteranceBanDTO]:
        return list(self._bundle.utterance_bans)

    def action_vocabulary(self) -> list[str]:
        return list(self._bundle.action_vocab)

    def fragments(self) -> list[FragmentDTO]:
        return list(self._bundle.fragments)

    def entry_lines(self) -> list[str]:
        return list(self._bundle.entry_lines)

    def morning_line(self, damage_level: int) -> str:
        lines = self._bundle.morning_lines
        if damage_level in lines:
            return lines[damage_level]
        return lines.get(0, "")

    def prompt_fragment(self, role: str) -> str:
        return self._bundle.prompt_fragments.get(role, "")
