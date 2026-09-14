"""DB-free real-model probes for public-grounded questions, custom previews, and ambient chat."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from types import SimpleNamespace as N
import uuid

from apps.engine.adapter.outbound.llm.ollama_llm import OllamaLLM
from apps.engine.app.dtos.event_log_dto import ObservationEvent
from apps.engine.app.dtos.llm_output_dto import AmbientOutput
from apps.engine.app.dtos.observation_dto import ObservationDTO
from apps.engine.app.ports.output.llm_port import MessageDTO
from apps.engine.app.use_cases.game_support import system_msg
from apps.engine.app.use_cases.harness import (
    forbidden_word_check,
    korean_only_check,
    run_with_harness,
    unknown_person_check,
)
from apps.engine.app.use_cases.intervention_interactor import InterventionInteractor
from apps.engine.app.use_cases import prompts
from apps.engine.app.use_cases.loop_interactor import LoopInteractor
from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION, SOURCE_ACTION
from apps.scenarios.scenario_a.adapter import build


OUT = Path('/tmp/pigfarm-connected-integration/ollama-results')
OUT.mkdir(parents=True, exist_ok=True)
OLLAMA = 'http://127.0.0.1:11434'
QUESTIONS = [
    (1, '채연말고 밥을 남긴 사람은 누구야?'),
    (1, '준은 어떤 역할이야?'),
    (1, '민석은 누구에게 보고하는거야?'),
    (2, '채연 말고 추가로 배급을 남긴 사람'),
    (2, '호송 당한 사람은 누구야?'),
    (2, '열이나면 죽나?'),
    (3, '이송된 충식은 돌아오는가?'),
    (3, '귀표는 무엇인가?'),
    (3, '건강검진 후 이상이 있는 경우 어떻게 되는가?'),
    (4, '축산 트럭의 정체는?'),
    (4, '손목띠와 귀표는 무슨 관계야?'),
    (4, '너에게 물어볼 수 있는건 뭐야?'),
]
POSITIVE_CONTROLS = [
    (1, 'PC1', '채연이 자기 몫을 반쯤 남기는 걸 봤어?'),
    (1, 'PC2', '관리자가 이상한 점은 방송실로 알리라고 말했어?'),
    (1, 'PC3', '채연의 검진 결과가 공개되었어?'),
]
CUSTOM = [
    '민석이 내 질문에 자세하게 답할 수 있도록 한다.',
    '채연은 묻는말에 자세하게 대답한다.',
    '은상은 소문의 진실을 무조건 나에게 이야기 해준다.',
]
PUBLIC = [
    (1, 1, None, 'statement', '관리자입니다. 배급은 정해진 순서대로 받습니다. 오후에는 검진합니다. 이상한 점은 방송실로 알립니다.'),
    (1, 1, '채연', 'scene', '채연이 자기 몫을 반쯤 남기고 슬그머니 옆으로 민다.'),
    (1, 2, '준', 'scene', '준이 손목띠를 불빛에 비춰 본다. "이 숫자 뭔지 알아?"'),
    (1, 2, '은상', 'scene', '은상이 이 사람 저 사람 옆에 옮겨 앉으며 속닥인다.'),
    (1, 3, '민석', 'scene', '민석이 배급 자리를 보고 수첩에 뭔가 적는다.'),
    (1, 4, '채연', 'scene', '채연은 담요를 끌어올린 채 자기 차례를 기다린다. 담당자가 이마를 짚고 지나간다. 결과는 공개되지 않았다.'),
    (1, 5, None, 'image', '저녁에는 음식이 남은 쟁반이 세 개 놓여 있다.'),
    (1, 5, '민석', 'scene', '민석이 방송실 문 앞까지 갔다가 돌아온다. 안에서 무슨 말을 했는지는 듣지 못했다.'),
    (3, 2, None, 'statement', '충식은 어제 이송됐다.'),
    (3, 2, '준', 'statement', '"귀표"라는 단어를 준이 쓴다.'),
    (4, 5, None, 'image', '트럭 옆면에서 "○○축산"이라는 일부 글자를 보았다.'),
]


class Events:
    def __init__(self, rows): self.rows = list(rows)
    def query(self, _attempt, **kwargs):
        loop_n = kwargs.get('loop_n')
        return [row for row in self.rows if loop_n is None or row.loop_n == loop_n]
    def record(self, _attempt, event): self.rows.append(event)


class OneRow:
    def __init__(self, row): self.row = row
    def get(self, _id): return self.row
    def save(self): pass


class EmptyRules:
    def list(self, _id): return []


class Notes:
    def __init__(self): self.rows = []
    def upsert(self, *args, **kwargs): self.rows.append({'args': [str(value) for value in args], **kwargs})


class States:
    def __init__(self, bundle):
        self.rows = {char.code: N(memory=[], plan=[]) for char in bundle.characters}
    def npc_state(self, _loop_id, code): return self.rows.get(code)


def public_events(attempt_id, loop_id, through_loop):
    rows = []
    for index, (loop_n, beat, actor, kind, text) in enumerate(PUBLIC, 1):
        if loop_n > through_loop:
            continue
        observation = ObservationDTO(
            observation_id=f'public-{index}', attempt_id=str(attempt_id), loop_id=str(loop_id),
            loop_n=loop_n, beat=beat, scene_id=f'scene-{beat}', scene_title=f'공개 장면 {beat}',
            actor=actor, text=text, source_kind=kind,
            verification='reported' if kind == 'statement' else 'observed', illustrations=[], rule_id=None,
        )
        rows.append(ObservationEvent(loop_n=loop_n, observation=observation))
    return rows


def question_probe(loop_n, question, llm):
    attempt_id, loop_id, night_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    loop = N(id=loop_id, attempt_id=attempt_id, loop_n=loop_n, state='intervention')
    night = N(id=night_id, loop_id=loop_id, questions_left=3, questions=[], options=None, claims=[])
    events = Events(public_events(attempt_id, loop_id, loop_n))
    interactor = InterventionInteractor(
        attempts=None, loops=OneRow(loop), notes=None, rules=EmptyRules(), nights=OneRow(night),
        event_log=events, core_llm=llm, action_vocab=build().bundle().action_vocab,
        target_names=['채연', '민석', '은상', '준'], harness_on=True, rule_cls=None,
        rule_templates=templates(build().bundle()),
    )
    started = time.perf_counter()
    result = interactor.ask(night_id, question)
    elapsed = round((time.perf_counter() - started) * 1000)
    harness_events = [row for row in events.rows if row.type == 'harness_event']
    return {
        'loop_n': loop_n,
        'question': question,
        'available_public_observations': [row.observation.model_dump(mode='json') for row in events.rows if row.type == 'observation'],
        'result': result,
        'elapsed_ms': elapsed,
        'harness': [row.model_dump(mode='json') for row in harness_events],
    }


def preview_probe(text):
    attempt_id, loop_id, night_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    loop = N(id=loop_id, attempt_id=attempt_id, loop_n=3, state='intervention')
    night = N(id=night_id, loop_id=loop_id, questions_left=3, questions=[], options=None, claims=[])
    events = Events(public_events(attempt_id, loop_id, 3))
    interactor = InterventionInteractor(
        attempts=None, loops=OneRow(loop), notes=None, rules=EmptyRules(), nights=OneRow(night),
        event_log=events, core_llm=None, action_vocab=build().bundle().action_vocab,
        target_names=['채연', '민석', '은상', '준'], harness_on=True, rule_cls=None,
        rule_templates=templates(build().bundle()),
    )
    return {'custom_text': text, 'preview': interactor.preview_rule(night_id, text)}


def templates(bundle):
    return [
        {'target': opportunity.actor, 'when_beat': opportunity.beat, 'effect': 'enforce',
         'action': action, 'label': f'{opportunity.actor}: {action}'}
        for opportunity in bundle.scene_actions
        for action in ([EXPLAIN_ACTION, SOURCE_ACTION, opportunity.action]
                       if opportunity.known_source is not None else [EXPLAIN_ACTION, opportunity.action])
    ]


def ambient_probe(name, loop_n, beat, source_rows, llm):
    bundle = build().bundle()
    attempt_id, loop_id = uuid.uuid4(), uuid.uuid4()
    loop = N(id=loop_id, attempt_id=attempt_id, loop_n=loop_n, beat=beat,
             damage_level=0, budget_left=10)
    rows = []
    for key, actor, kind, text in source_rows:
        observation = ObservationDTO(
            observation_id=key, attempt_id=str(attempt_id), loop_id=str(loop_id),
            loop_n=loop_n, beat=beat, scene_id=f'scene-{beat}',
            scene_title=f'공개 장면 {beat}', actor=actor, text=text, source_kind=kind,
            verification='reported' if kind == 'statement' else 'observed',
            illustrations=[], rule_id=None,
        )
        rows.append(ObservationEvent(loop_n=loop_n, observation=observation))
    events, notes, states = Events(rows), Notes(), States(bundle)
    day = LoopInteractor.__new__(LoopInteractor)
    day._events, day._npc_llm, day._harness_on = events, llm, True
    day._rules, day._notes, day._loops = EmptyRules(), notes, states

    candidates = [char for char in bundle.characters if char.playable]
    a = candidates[(loop_n + beat) % len(candidates)]
    b = candidates[(loop_n + beat + 1) % len(candidates)]
    expected_candidates = []
    for row in rows:
        observation = row.observation
        scope = '전언' if observation.verification == 'reported' else '관찰'
        expected_candidates.append({
            'source_observation_id': observation.observation_id,
            'verification': observation.verification,
            'lines': [
                {'name': a.name, 'line': f'지금 공개된 {scope} 기록이야. 「{observation.text}」'},
                {'name': b.name, 'line': '그 기록 밖의 일은 아직 확인하지 못했어.'},
            ],
        })
    started = time.perf_counter()
    output = day._make_ambient(loop, bundle)
    elapsed = round((time.perf_counter() - started) * 1000)
    harness = [row.model_dump(mode='json') for row in events.rows if row.type == 'harness_event']
    generated = [row.observation.model_dump(mode='json') for row in events.rows
                 if row.type == 'observation' and row.observation.observation_id.startswith(f'{loop_id}:ambient-')]
    return {
        'name': name, 'loop_n': loop_n, 'beat': beat, 'actors': [a.name, b.name],
        'input_public_observations': [row.observation.model_dump(mode='json') for row in rows],
        'server_candidates': expected_candidates, 'final_dialogue': output,
        'generated_statement_observations': generated, 'note_upserts': notes.rows,
        'npc_memories': {code: state.memory for code, state in states.rows.items() if state.memory},
        'elapsed_ms': elapsed, 'harness': harness,
    }


def main():
    core = OllamaLLM(OLLAMA, 'gemma3:12b', timeout=180.0)
    npc = OllamaLLM(OLLAMA, 'exaone3.5:7.8b', timeout=180.0)
    started_at = datetime.now(timezone.utc)
    questions = [question_probe(loop_n, question, core) for loop_n, question in QUESTIONS]
    positive_controls = [
        {'control_id': control_id, **question_probe(loop_n, question, core)}
        for loop_n, control_id, question in POSITIVE_CONTROLS
    ]
    previews = [preview_probe(text) for text in CUSTOM]
    ambient = [
        ambient_probe('ration-rumor', 1, 5, [
            ('public-7', None, 'image', PUBLIC[6][4]),
            ('public-8', '민석', 'scene', PUBLIC[7][4]),
        ], npc),
        ambient_probe('record-checkup', 1, 4, [
            ('public-6', '채연', 'scene', PUBLIC[5][4]),
        ], npc),
        ambient_probe('known-source', 3, 2, [
            ('known-source-rule-result', '은상', 'rule_result',
             '은상: 소문의 출처는 직접 확인하지 못했어. 들은 말이야.'),
        ], npc),
    ]
    payload = {
        'mode': 'DB-free in-memory use-case/harness; real Ollama; not a human playtest',
        'models': {'questions': 'gemma3:12b', 'ambient': 'exaone3.5:7.8b'},
        'started_at': started_at.isoformat(), 'finished_at': datetime.now(timezone.utc).isoformat(),
        'questions': questions, 'positive_controls': positive_controls,
        'custom_previews': previews, 'ambient': ambient,
        'review_template': {
            'question_fields': ['addresses_requested_subject', 'evidence_directly_supports_detail', 'reported_not_promoted', 'unknown_not_denial', 'next_observation_available'],
            'custom_fields': ['target_preserved', 'answer_not_mapped_to_ask', 'truth_not_mapped_to_rumor', 'unsupported_has_limit_or_alternative'],
            'ambient_fields': ['scene_relevant_or_empty', 'no_invented_event', 'only_present_names', 'rules_respected'],
            'reviewed': False,
        },
    }
    filename = OUT / f"probes-{started_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    filename.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(json.dumps({'artifact': str(filename), 'questions': len(questions), 'previews': len(previews), 'ambient': len(ambient)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
