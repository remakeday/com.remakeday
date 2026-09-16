"""Bounded thinking diagnostic on three unchanged archived NPC prompts."""
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
out = ROOT / 'output/npc-dialogue-2026-09-15/thinking-intervention.json'
archive = json.loads(source.read_text())
settings = get_settings()
report = {'intervention': {'think': True, 'num_predict': 1024},
          'baseline': str(source.relative_to(ROOT)), 'harness_run': False,
          'game_state_writes': False, 'comparisons': []}
for case_id, phase in [('past-loop-minseok', 'followup'), ('core-6', 'primary'), ('core-7', 'followup')]:
    case = next(r for r in archive['results'] if r['case']['id'] == case_id)
    turn = next(t for t in case['turns'] if t['phase'] == phase)
    call = turn['harness'][0]['call_records'][0]
    body = {'model': archive['model'], 'messages': deepcopy(call['messages']),
            'stream': False, 'keep_alive': '2h', 'format': archive['output_schemas']['agent'],
            'think': True, 'options': {'temperature': call['temperature'], 'num_predict': 1024}}
    started = perf_counter()
    result = httpx.post(settings.ollama_base_url.rstrip('/') + '/api/chat', json=body, timeout=120)
    result.raise_for_status()
    data = result.json()
    elapsed = round((perf_counter() - started) * 1000, 2)
    content = data.get('message', {}).get('content', '')
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        parsed = None
    comparison = {'case': case_id, 'phase': phase, 'baseline_output': call['output'],
                  'modified_request': body, 'modified_response': data,
                  'elapsed_ms': elapsed, 'parsed_json': parsed,
                  'reasoning_characters': len(data.get('message', {}).get('thinking', '')),
                  'reasoning_token_count': data.get('thinking_eval_count'),
                  'token_count_note': 'eval_count is preserved from provider; separate reasoning-token count is null when not reported.'}
    report['comparisons'].append(comparison)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({'case': case_id, 'elapsed_ms': elapsed, 'done_reason': data.get('done_reason'),
                     'eval_count': data.get('eval_count'), 'reasoning_characters': comparison['reasoning_characters'],
                     'parsed_json': parsed, 'content': content}, ensure_ascii=False), flush=True)
