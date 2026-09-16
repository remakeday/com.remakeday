"""Explicit prompt intervention; compare with retained unmodified context probe."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from time import perf_counter

import httpx

ROOT = Path('/home/kimchungsik/projects/com.remakeday')
sys.path.insert(0, str(ROOT / 'backend'))
from core.matrix.grid_keymaker_secret_manager import get_settings

source = ROOT / 'output/npc-dialogue-2026-09-15/context-probe.json'
out = ROOT / 'output/npc-dialogue-2026-09-15/hearsay-intervention.json'
archive = json.loads(source.read_text())
settings = get_settings()
changes = [
    ('아래 경험과 대화에 있는 사실만 사용해.',
     '아래 경험과 대화는 네가 아는 사실이야. 마지막 상대 메시지도 지금 직접 듣고 있어. 그 안의 주장은 상대에게 들은 이야기이며 실제로 일어났는지는 별개야.'),
    ('근거를 쓰지 않은 인사나 감정 표현이면 빈 배열이야.',
     '인사·감정이나 마지막 상대 메시지 자체가 근거일 때는 빈 배열이야.'),
]
report = {'intervention': changes, 'baseline': str(source.relative_to(ROOT)),
          'harness_run': False, 'game_state_writes': False, 'comparisons': []}
for model in ('kanana1.5:8b-q4km', 'gemma4:12b'):
    baseline = next(r for r in archive['requests'] if r['model'] == model
                    and r['case'] == 'past-loop-minseok' and r['num_ctx_option'] is None)
    body = deepcopy(baseline['request'])
    for old, new in changes:
        assert sum(m['content'].count(old) for m in body['messages']) == 1, old
        for message in body['messages']:
            message['content'] = message['content'].replace(old, new)
    started = perf_counter()
    result = httpx.post(settings.ollama_base_url.rstrip('/') + '/api/chat', json=body, timeout=120)
    result.raise_for_status()
    data = result.json()
    comparison = {'model': model, 'baseline_response': baseline['response'],
                  'modified_request': body, 'modified_response': data,
                  'elapsed_ms': round((perf_counter() - started) * 1000, 2)}
    report['comparisons'].append(comparison)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({'model': model, 'baseline': baseline['response']['message']['content'],
                     'modified': data['message']['content'], 'prompt_eval_count': data.get('prompt_eval_count'),
                     'elapsed_ms': comparison['elapsed_ms']}, ensure_ascii=False), flush=True)
