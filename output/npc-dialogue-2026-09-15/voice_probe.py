"""Three archived-prompt interventions; no runtime files or game state changed."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from time import perf_counter

import httpx

ROOT = Path('/home/kimchungsik/projects/com.remakeday')
sys.path.insert(0, str(ROOT / 'backend'))
from core.matrix.grid_keymaker_secret_manager import get_settings

source = ROOT / 'output/npc-dialogue-2026-09-15/gemma-final-comparison.json'
out = ROOT / 'output/npc-dialogue-2026-09-15/voice-intervention.json'
archive = json.loads(source.read_text())
settings = get_settings()
old = ('일곱 살 아이처럼 쉬운 말로 편하게 이야기해. 짧은 반말 한두 문장이면 좋아. 이유를 설명할 때는 더 말해도 돼.\n'
       '궁금한 것과 네 마음을 솔직하게 말해. 아는 것은 답하고, 모르는 부분만 "그건 나도 몰라"처럼 네 말로 표현해.')
new = '친구에게 말하듯 쉽고 자연스러운 반말로 이야기해. 질문에 맞춰 네 경험과 행동의 이유를 설명해. 짧은 한두 문장이면 좋아. 이유를 설명할 때는 더 말해도 돼.'
report = {'intervention': {'before': old, 'after': new}, 'baseline': str(source.relative_to(ROOT)),
          'harness_run': False, 'game_state_writes': False, 'comparisons': []}
for case_id, phase in [('past-loop-minseok', 'followup'), ('core-6', 'primary'), ('core-7', 'followup')]:
    case = next(r for r in archive['results'] if r['case']['id'] == case_id)
    turn = next(t for t in case['turns'] if t['phase'] == phase)
    call = turn['harness'][0]['call_records'][0]
    messages = deepcopy(call['messages'])
    assert sum(m['content'].count(old) for m in messages) == 1
    for message in messages:
        message['content'] = message['content'].replace(old, new)
    body = {'model': archive['model'], 'messages': messages, 'stream': False, 'keep_alive': '2h',
            'format': archive['output_schemas']['agent'], 'think': False,
            'options': {'temperature': call['temperature']}}
    started = perf_counter()
    result = httpx.post(settings.ollama_base_url.rstrip('/') + '/api/chat', json=body, timeout=120)
    result.raise_for_status()
    data = result.json()
    comparison = {'case': case_id, 'phase': phase, 'baseline_output': call['output'],
                  'modified_request': body, 'modified_response': data,
                  'elapsed_ms': round((perf_counter() - started) * 1000, 2)}
    report['comparisons'].append(comparison)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({'case': case_id, 'baseline': call['output'], 'modified': data['message']['content'],
                     'prompt_eval_count': data.get('prompt_eval_count'), 'elapsed_ms': comparison['elapsed_ms']},
                    ensure_ascii=False), flush=True)
