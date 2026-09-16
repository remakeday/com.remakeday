from enum import StrEnum


class EventType(StrEnum):
    """부록 C 로그 스키마의 17개 이벤트 타입."""

    SESSION_START = "session_start"
    LOOP_START = "loop_start"
    UTTERANCE = "utterance"
    TOOL_CALL = "tool_call"
    MANAGER_CHECK = "manager_check"
    MONKEY_PAW_OFFER = "monkey_paw_offer"
    ANSWER_DRAFT = "answer_draft"
    ANSWER_NORMALIZED = "answer_normalized"
    ANSWER_SCORED = "answer_scored"
    ANSWER_WRONG_CLAIMS = "answer_wrong_claims"
    DEATH = "death"
    INTERVENTION_QUESTION = "intervention_question"
    INTERVENTION_OPTIONS = "intervention_options"
    RULE_APPLIED = "rule_applied"
    LOOP_END = "loop_end"
    COOKIE_SHOWN = "cookie_shown"
    SESSION_END = "session_end"
    # 부록 C 17종 + 모델정책 v1 §9의 하네스 로그 (18번째)
    HARNESS_EVENT = "harness_event"
    OBSERVATION = "observation"
    RULE_EXECUTION = "rule_execution"
    RULE_PREVIEW = "rule_preview"
    GUARD = "guard"
