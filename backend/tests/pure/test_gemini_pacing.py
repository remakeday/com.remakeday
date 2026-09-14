from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from types import SimpleNamespace as NS

from apps.engine.adapter.outbound.llm import gemini_llm


def test_concurrent_instances_share_six_second_start_spacing(monkeypatch):
    now, starts, guard = [0.0], [], Lock()
    monkeypatch.setattr(gemini_llm, "monotonic", lambda: now[0])
    monkeypatch.setattr(gemini_llm, "sleep", lambda seconds: now.__setitem__(0, now[0] + seconds))
    monkeypatch.setattr(gemini_llm, "_last_request_at", None)
    def generate(**kwargs):
        with guard:
            starts.append(now[0])
        return NS(prompt_feedback=None, candidates=[], text='{}')
    monkeypatch.setattr(gemini_llm.genai, "Client", lambda **kwargs: NS(models=NS(generate_content=generate)))
    adapters = [gemini_llm.GeminiLLM("test", "model") for _ in range(4)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(lambda llm: llm.complete([], {}), adapters)) == [{}, {}, {}, {}]
    assert sorted(starts) == [0, 6, 12, 18]


def test_provider_error_still_consumes_a_shared_slot_and_custom_rate(monkeypatch):
    from apps.engine.app.dtos.llm_output_dto import AdvisorInterpretationOutput
    from apps.engine.app.use_cases.harness import run_with_harness
    now, sleeps = [0.0], []
    monkeypatch.setattr(gemini_llm, "monotonic", lambda: now[0])
    def wait(seconds):
        sleeps.append(seconds); now[0] += seconds
    monkeypatch.setattr(gemini_llm, "sleep", wait)
    monkeypatch.setattr(gemini_llm, "_last_request_at", None)
    def fail(**kwargs): raise RuntimeError("provider error")
    monkeypatch.setattr(gemini_llm.genai, "Client", lambda **kwargs: NS(models=NS(generate_content=fail)))
    for _ in range(2):
        llm = gemini_llm.GeminiLLM("test", "model", requests_per_minute=5)
        _, report = run_with_harness(llm, [], AdvisorInterpretationOutput, role="advisor")
        assert report.attempts == 1 and report.fallback_used
    assert sleeps == [12]
