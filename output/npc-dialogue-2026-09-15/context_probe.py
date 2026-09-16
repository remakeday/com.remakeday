"""Replay archived NPC messages and retain Ollama context/timing metadata.

No engine state is changed. A response here has not passed the game harness.
"""
import json
from pathlib import Path
import sys
from time import perf_counter

import httpx

ROOT = Path('/home/kimchungsik/projects/com.remakeday')
sys.path.insert(0, str(ROOT / 'backend'))
from core.matrix.grid_keymaker_secret_manager import get_settings

OUT = ROOT / 'output/npc-dialogue-2026-09-15/context-probe.json'
SETTINGS = get_settings()
CHOICES = [('core-7', 'primary'), ('past-loop-minseok', 'followup'), ('targeted-deletion', 'followup')]
report = {'purpose': 'Same archived messages/schema/temperature; compare omitted num_ctx with num_ctx=8192.',
          'harness_run': False, 'game_state_writes': False, 'requests': []}

for short in ('kanana', 'gemma'):
    path = ROOT / f'output/npc-dialogue-2026-09-15/{short}-short-ids.json'
    archive = json.loads(path.read_text())
    for case_id, phase in CHOICES:
        case = next(r for r in archive['results'] if r['case']['id'] == case_id)
        turn = next(t for t in case['turns'] if t['phase'] == phase)
        call = turn['harness'][0]['call_records'][0]
        for context in (None, 8192):
            body = {'model': archive['model'], 'messages': call['messages'], 'stream': False,
                    'keep_alive': '2h', 'options': {'temperature': call['temperature']},
                    'format': archive['output_schemas']['agent']}
            think = archive['model_parameters']['think']
            if think is not None:
                body['think'] = think
            if context is not None:
                body['options']['num_ctx'] = context
            started = perf_counter()
            response = httpx.post(SETTINGS.ollama_base_url.rstrip('/') + '/api/chat', json=body, timeout=120)
            response.raise_for_status()
            data = response.json()
            entry = {'archive': str(path.relative_to(ROOT)), 'case': case_id, 'phase': phase,
                     'model': archive['model'], 'num_ctx_option': context,
                     'request': body, 'response': data,
                     'elapsed_ms': round((perf_counter() - started) * 1000, 2)}
            report['requests'].append(entry)
            OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2))
            print(json.dumps({k: v for k, v in entry.items() if k not in ('request', 'response')} |
                             {k: data.get(k) for k in ('prompt_eval_count', 'eval_count', 'load_duration', 'total_duration')} |
                             {'content': data['message']['content']}, ensure_ascii=False), flush=True)
