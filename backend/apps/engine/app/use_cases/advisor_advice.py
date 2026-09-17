"""신의 질문 답변 조립 — 판정·조언은 결정론, 진실은 모른다 (기획서 §7.1·§7.4)."""

import re

from apps.engine.domain.value_objects.game_constants import LADDER_SCORE_STEPS, QUESTION_REFUNDS_PER_NIGHT

_WHY_CUES = ("왜", "이유", "어떻게", "어째서", "뭐 때문")
_POLITE_RE = re.compile(r"(습니다|합니다|입니다)")
_CONFIRM_RE = re.compile(r"확인(했|됐|되었|하였)")

WHY_PREFIX = "왜인지는 내가 말할 수 없다. 그 전에 일어난 일은 말할 수 있다."
_VERDICT = {"supported": "맞다.", "contradicted": "아니다.", "unknown": "그건 알 수 없다."}
_LEADING_VERDICT_RE = re.compile(r"^(맞다|아니다|틀리다|그건 알 수 없다|그런 일은 없었다)[.!,]?\s*")
# 무엇·누구 등을 묻는 질문은 예/아니오로 판정하지 않는다. "언제나·누구든" 같은 부사형은 제외.
_WH_RE = re.compile(r"(무엇|뭐|뭘|뭔|누구|누가|어디|언제|무슨|몇|어느|어떤)(?!나|든)")
# 본문이 스스로 확답을 피하면 앞에 "맞다./아니다."를 붙이지 않는다.
_HEDGE_CUES = ("알 수 없", "가능성", "확인이 필요", "확인되지 않", "모른다", "모르겠", "불분명", "단정할 수 없", "확실치 않", "확실하지 않")


def strip_leading_verdict(text: str) -> str:
    """모델 답변 선두의 판정어를 제거 — 시스템이 앞에 붙이는 verdict와 중복되지 않게."""
    return _LEADING_VERDICT_RE.sub("", text, count=1)


def is_why_question(text: str) -> bool:
    return any(cue in text for cue in _WHY_CUES)


def is_wh_question(text: str) -> bool:
    return bool(_WH_RE.search(text))


def is_hedged(answer: str) -> bool:
    return any(cue in answer for cue in _HEDGE_CUES)


def settle_status(status: str, question: str, answer: str, *, lookup: bool) -> str:
    """근거 relation은 하위 사실만 받칠 수 있다 — 본문이 확답을 피하거나 예/아니오 질문이 아니면 unknown으로 낮춘다."""
    if status == "contradicted" and (lookup or is_wh_question(question)):
        return "unknown"
    if status != "unknown" and is_hedged(answer):
        return "unknown"
    return status


def verdict_prefix(status: str, why: bool, wh: bool = False) -> str:
    if why:
        return WHY_PREFIX
    if wh and status == "supported":
        return ""
    return _VERDICT.get(status, _VERDICT["unknown"])


def polite_register_check(out) -> str | None:
    if _POLITE_RE.search(str(getattr(out, "answer", "") or "")):
        return "register: 합니다체"
    return None


def unbacked_confirmation_check(out) -> str | None:
    answer = str(getattr(out, "answer", "") or "")
    if _CONFIRM_RE.search(answer) and not list(getattr(out, "evidence", []) or []):
        return "unbacked_confirmation"
    return None


def find_anchor(lead, observations):
    """플레이어 공개 관찰에서 anchor_cues 중 하나라도 text에 포함된 가장 최근(리스트 뒤쪽) 관찰을 찾는다."""
    for observation in reversed(list(observations)):
        if any(cue in observation.text for cue in lead.anchor_cues):
            return observation
    return None


def advice_sentence(lead, anchor) -> str:
    """닻이 되는 관찰과 함께 조언 문장을 조립한다."""
    head = f"네 기록의 「{anchor.text}」."
    if lead.ask:
        return f"{head} 내일 {lead.target}에게 {lead.ask} 물어봐라."
    return f"{head} {lead.target}: {lead.rule_action} 규칙을 걸어 봐라."


# ── 안내 질문 — 게임 목적·사용법은 판정하지 않고 안내로 답한다 (테스터10 F5) ──
# 원인·동기를 밝혀 쓰는 게임이라는 수준까지만. 정체·부작용 칸과 점수 기준은 말하지 않는다 (기획서 §4.4⑤).
# 안내 답 문구는 초안 — 시나리오 디렉터 확인 전
GUIDE_ANSWERS = {
    "purpose": ("세계는 오늘 밤 멸망하고, 너는 다섯 번의 하루 안에 왜 멸망했는지 알아내야 한다. "
                "밤마다 무슨 일이 원인이었는지, 누가 왜 그렇게 했는지 써라. "
                "낮에는 사람들에게 묻고, 밤에는 나에게 기록을 확인하고, 규칙 하나로 다음 하루를 실험해라."),
    "usage": ("가설을 넣어 물으면 맞다·아니다로 판정한다. 누가·무엇을 물으면 기록에서 찾아 준다. "
              "기록으로 판단할 수 없으면 알 수 없다고 답하고, 그 질문은 한 밤 세 번까지 횟수에서 빼 준다."),
}
_LEAD_IN = r"^(?:그래서|그럼|근데|이제)?\s*"
# "뭘 해야/하면" 뒤에는 짧은 어미·문장 끝만 — "뭘 하면 이송돼?"처럼 세계 사건이 오면 판정 질문이다 (opus 리뷰 I1)
_TASK_END = r"\s*(?:돼|되지|될까|해|하지|할까|하나|하냐|하는\s*거야)?요?\s*[?？.!~]*$"
# 사용법 말 뒤에는 그 문장의 짧은 끝만 — 문장부호 뒤에 다른 질문이 붙으면("…물어봐도 돼? 트럭 언제 와") 판정 질문이다
_USAGE_END = r"[^?？.!]{0,10}[?？.!~\s]*$"
# 위에서부터 첫 적중 분류 — 판단 근거는 계획서 2026-09-18 §3(b) 표
_GUIDE_TABLE = (
    ("purpose", re.compile(r"게임")),  # 인물 발화 금칙어라 기록에 없다 — 항상 메타 질문
    ("purpose", re.compile(_LEAD_IN + r"(?:이\s*게임의?|내|나의|우리의?)?\s*(?:목적|목표)[이은는가]?\s*(?:뭐|뭔|무엇)")),
    ("purpose", re.compile(r"멸망(?:한다는|한다니|이라는|이란|이|은)\s*(?:게|건|거|것이?)?\s*(?:뭐|뭔|무슨|무엇)")),
    ("purpose", re.compile(_LEAD_IN + r"(?:나는|내가|난|나|우리는?)?\s*(?:뭘|뭐를?|무엇을)\s*(?:해야|하면)" + _TASK_END)),
    ("usage", re.compile(r"(?:너에게|너한테|네게|신에게|당신에게).*(?:물어|질문)" + _USAGE_END)),
    ("usage", re.compile(r"(?:(?:질문|묻는|물어보는)(?:하는)?\s*(?:법|방법)|" + _LEAD_IN
                         + r"(?:뭘|뭐를?|무엇을|어떻게)\s*(?:물어|질문))" + _USAGE_END)),
)


# 이름 뒤에 올 수 있는 조사·호격 — 이 뒤로 한글이 더 이어지면 이름이 아니다("준비·준수"의 준)
_NAME_TAIL = (r"(?:이)?(?:한테서|에게서|한테|에게|께서|께|랑|하고|처럼|보다|까지|부터|으로|로|"
              r"야|아|가|는|은|를|을|의|도|만|과|와)?(?![가-힣])")


def _mentions(question: str, name: str) -> bool:
    return bool(re.search(rf"(?<![가-힣]){re.escape(name)}{_NAME_TAIL}", question))  # "기준"의 준도 이름이 아니다


def guide_kind(text: str, names: list[str]) -> str | None:
    """안내 질문이면 분류 이름, 세계 질문이면 None. 인물 이름이 있으면 세계 질문이다."""
    question = " ".join(text.split())
    if any(_mentions(question, name) for name in names):
        return None
    return next((kind for kind, pattern in _GUIDE_TABLE if pattern.search(question)), None)


# ── 환급 — "알 수 없다"는 헛걸음으로 만들지 않는다 (테스터9 F19) ──
_QUESTION_NOISE_RE = re.compile(r"[\s.,!?~…\"'「」]")


def _same_question_key(text: str) -> str:
    return _QUESTION_NOISE_RE.sub("", text)


def refund_question(status: str, text: str, previous_questions: list[str], *, refunds_used: int,
                    cap: int = QUESTION_REFUNDS_PER_NIGHT) -> bool:
    """unknown이고, 같은 밤 상한 안이고, 같은 밤에 이미 한 질문(공백·문장부호 무시)이 아니면 환급한다."""
    key = _same_question_key(text)
    return (status == "unknown" and refunds_used < cap
            and all(_same_question_key(q) != key for q in previous_questions))


# ── 공개 사다리 — 회차 바닥 + 점수로 한 칸씩 앞당김, 열린 칸은 닫히지 않는다 ──
def ladder_stage(loop_n: int, best_total: float, steps=LADDER_SCORE_STEPS) -> int:
    return max(loop_n, 1 + sum(best_total >= step for step in steps))


def open_rungs(ladder, stage: int, text: str, limit: int = 2) -> list:
    """열린 칸 중 질문이 cue를 묻는 칸만, 단계 높은 순으로."""
    matched = [rung for rung in ladder if rung.stage <= stage and any(cue in text for cue in rung.cues)]
    return sorted(matched, key=lambda rung: -rung.stage)[:limit]
