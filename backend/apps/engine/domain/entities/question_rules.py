"""A finite player-question condition, kept separate from autonomous scene actions."""

import re


REPORT_QUESTION_ACTION = "보고를 물으면 자신이 한 일을 자세히 설명한다"


def is_question_action(action: str) -> bool:
    return action == REPORT_QUESTION_ACTION


def report_question_rule(text: str, target: str) -> dict | None:
    # Full matching matters: an extra recipient, time or negation cannot disappear.
    if re.search(r"내가\s*보고(?:한|하는)", text):
        return None
    pattern = (
        re.escape(target) + r"[은는이가]?\s*(?:내가\s*)?"
        r"보고(?:하는\s*(?:것|내용)|한\s*(?:것|내용)|\s*내용)?"
        r"(?:[을를]|에\s*(?:관해|대해))?\s*(?:내가\s*)?"
        r"(?:물어보면|물으면|질문하면|질문할\s*때)\s*"
        r"(?:자신이\s*보고한\s*내용을\s*)?"
        r"(?:상세하게|자세히|구체적으로)\s*(?:설명한다|말한다|답한다)\s*[.]?"
    )
    if not re.fullmatch(pattern, text.strip()):
        return None
    return {"target": target, "when_beat": "any", "effect": "enforce",
            "action": REPORT_QUESTION_ACTION,
            "label": f"{target}은 내가 보고에 관해 물으면, 자신이 보고한 내용을 자세히 설명한다."}


def question_matches(action: str, text: str) -> bool:
    if not is_question_action(action):
        return False
    # Preserve a player's explicit change of topic and distinguish 보다/신다 homonyms.
    text = text.rsplit("말고", 1)[-1].strip()
    request = "?" in text or re.search(r"(?:말해|설명해|알려|궁금|뭐|무엇|누구|왜|어떻게)", text)
    if not request and not re.search(r"(?:했어|했니|했나|하니|하냐|하는데|한 거야)[.!]?\s*$", text):
        return False
    report = re.search(r"(?:보고|신고)(?:\s*(?:내용|얘기|이야기|안\s*했)|했|하|한|해|할|를|에|는|가)", text)
    message = "방송실" in text and re.search(r"(?:전했|알렸|말했|얘기했)", text)
    return bool(report or message)
