# NPC dialogue/persona redesign — independent review

Reviewed 2026-09-15, HEAD `09c3f23`, in-place uncommitted changes.

## Scope and method

Read the approved spec and implementation plan, `/tmp/remakeday-npc-review.diff`, its original dirty baseline `/tmp/remakeday-before-npc-change.diff`, the new memory/context modules, NPC regression tests, frontend follow-up test, and relevant surrounding transaction/event/context code. Existing unrelated changes (advisor leads, journey/ending changes, dormant actions themselves, etc.) are not attributed to this task.

This was a read-only review of the checkout. No commits, browser launches, external model calls, or database test reruns. Two small Python probes ran against pure functions to confirm the findings below. The coordinator's integration/browser/real-model results are separate evidence and were not rerun here.

## Strengths

- Structured day memories retain tombstones and calculate transitive masking. Replaying the same source ID cannot revive it, while a new independent source remains available.
- Direct dialogue and `ask_npc` now use the same persona, baseline knowledge, day-memory filtering, and output-ID checks. Player notes no longer flow automatically into NPC context.
- Scene participants receive explicit actor/witness perspectives; unavailable characters are filtered from baseline knowledge and day memory.
- A loop-row lock serializes direct dialogue and scene advancement. UUID-based replay returns the committed response before charging again; dialogue memory, observations, notes, event, and budget share a transaction.
- The frontend preserves the selected NPC and keeps an unresolved question's ID across service/network retries. A synchronous mutation guard protects against immediate double clicks, including retries.
- Harness audit events already use a separate session during scene transactions, preserving failed model-call records even when gameplay writes roll back.

## Issues

### Important — P2: NPC-to-NPC questions can restore deleted information

**Location:** `backend/apps/engine/app/use_cases/loop_interactor.py:436` (asker's memory write, lines 436–439).

The asker receives a memory containing both `내 질문: {tool_call.question}` and the target's answer, but the entry has no `source_ids`. The question can repeat facts from the asker's existing memories. If the manager later deletes one of those sources, this copy remains visible and restores the deleted fact in the next direct/`ask_npc` context.

**Reproduction:** The asker remembers `민석: 빨간 표식을 봤어.` under source `original`, asks `빨간 표식을 봤다고 했지?`, and gets `기억이 안 나.`. After `forget_memory(memory, 'original')`, the visible memory still contains `내 질문: 빨간 표식을 봤다고 했지?\n민석: 기억이 안 나.`. A pure probe of the same source-less `add_memory` write confirmed this. The answer provided no independent confirmation; the retained question alone revives the deleted assertion.

**Fix:** Preserve the originating dependencies on the asker's question. Separate the question from a genuinely independent new answer where necessary so that deletion masks derived information while still allowing new evidence to teach the fact again. Cover this through the real `ask_npc` use-case path, including a nonconfirming answer.

**Spec impact:** §4.3 and Task 1 require derived exchanges to stay hidden after source deletion and disallow restoring facts through another input path.

### Important — P2: Rule-generated and fragment speech never enters day memory

**Location:** `backend/apps/engine/app/use_cases/npc_context.py:28` (the learning loop only handles broadcast IDs and action IDs through line 50); call site `backend/apps/engine/app/use_cases/loop_interactor.py:576`.

`execute_scene` emits actual authored speech for information rules under `rule-{beat}-{rule_id}`, and `_disclose_scene` emits authored statement fragments. `learn_scene` ignores both categories. The public statement therefore lacks a corresponding memory for its speaker and explicit listeners. They cannot use it in follow-up context, and the manager cannot select that statement's ID for deletion. This is especially visible because the earlier blanket current-observation prompt was removed.

**Confirmed reproduction:** At beat 5, enforce `소문의 알려진 출처를 밝힌다` on 은상, execute the scene, then run `learn_scene` for all NPCs. The public statement is `은상: 준에게 들었어. 나는 직접 본 게 아니야.`. Its observation ID is absent from both 은상 and the explicit witness 민석's memories. 민석 retains only `은상이 사람들 사이를 오가며 귓속말을 한다.` and his own visit explanation, so the newly disclosed source is unavailable to his next answer.

The same omission applies to the existing loop-3 authored fragment `"귀표"라는 단어를 준이 쓴다.`: it is publicly recorded without becoming Jun's memory of saying it. It should have explicit speaker/listener metadata rather than extracting character identity from arbitrary text.

**Fix:** Learn authored speech for its explicit participants, with its own observation ID and appropriate action/source dependencies. Retain each speaker's actual speech and only deliver it to the defined listeners. Add coverage for a rule disclosure followed by direct/`ask_npc` questions and targeted deletion.

**Spec impact:** §4.2, §7.2, and Task 1 require participants' authored dialogue and rule disclosures to use the same source-addressed memory and masking contract as direct dialogue.

### Important — P2: Exact name validation rejects normal references to Jun

**Location:** `backend/apps/engine/app/use_cases/harness.py:153`.

The change to exact roster matching is appropriate, but the suffix normalization strips `이` only when the captured token has more than two characters. For the actual one-syllable NPC name `준`, normal Korean forms capture `준이` and are falsely classified as an invented person.

**Confirmed pure-function results:**

```text
규정이야. 방송에서 말했어. => accepted
준이가 말했어.            => unknown_person: '준이' in reply
준이가 그랬어.            => unknown_person: '준이' in reply
내 친구는 준이야.         => unknown_person: '준이' in reply
은상이가 말했어.          => accepted
```

This can trigger needless regeneration and ultimately a 503 for a correct response. It directly affects the newly specified rumor source, which is Jun.

**Fix:** Normalize the optional Korean suffix against known roster names, including one-syllable names, while keeping exact validation for the resulting name. Add these cases beside the regulation regression and invented-name tests.

## Critical / minor issues

No critical issue established. No style-only changes requested.

## Assessment

**Spec compliance: incomplete pending the two memory-path fixes.** The principal design is implemented, but derived NPC-to-NPC questions and authored rule/fragment speech still violate the shared memory contract.

**Code quality: ready after the three fixes above and focused regression checks.** The transaction/idempotency approach and frontend retry flow are coherent. The findings are localized; they do not require a new architecture or a broader refactor.

The real model's naturalness, factual interpretation, and response latency remain subject to the separate evaluation. This review does not claim that ID validity proves semantic correctness.

---

# Focused re-review of fixes — 2026-09-15

## Scope

Reviewed `/tmp/remakeday-npc-review-fixes.diff`, current `npc_context.py`/`npc_memory.py`, the three targeted fixes, the added conditional action-account mechanism, evidence-ID bracket normalization, and the added engine regression for the NPC-question deletion case. No database/browser/external-model calls or source edits were performed.

## Original findings

| Finding | Status | Evidence |
|---|---|---|
| Source-less NPC-to-NPC question restores deleted information | **Addressed** | `loop_interactor.py:436` now stores the newly heard answer separately; `:439` stores the originating question with dependencies on the asker's prior visible memories. `test_asking_friend_does_not_preserve_deleted_fact_inside_own_question` exercises the nonconfirming-answer case through `_run_ask_npc`. The database test was read, not rerun by this reviewer. |
| Rule/fragment speech missing from memories | **Addressed** | `npc_context.py:58` learns actual rule statements for the action's speaker and explicit witnesses, linked to the action source. `:69` learns explicitly attributed statement fragments. Jun's fragments now carry actor/witness metadata. Pure review probes verified speaker/witness learning, targeted deletion, and non-restoration on replay for rule and fragment speech. |
| Normal Jun suffixes falsely rejected | **Addressed** | `harness.py:153` normalizes the optional suffix against the actual roster. The three reported Jun examples pass; an invented `영수` reference remains rejected. |

## Conditional action accounts and related changes

- `actions_occurred` requires a matching observation from the current loop, no later than the current beat, with the expected actor, observed status, and exact executed narration. Suppressed action narration does not satisfy that condition.
- Minseok's conditional account names Chaeyeon only after her actual beat-3 ration action. A pure probe verified that suppression produces the generic account instead, and deleting the ration source also hides the derived record memory.
- Eunsang's actor account is selected only if the underlying rumor action occurred; suppressing that action takes the existing `하지 않은 일` branch.
- The new high-damage action filter prevents executing the explicit hearsay action whose narration would restore the lost character's name.
- Bracket normalization only changes the presentation of an evidence ID. The membership check against currently allowed IDs remains in place; it does not authorize unknown or hidden sources.

## Verification in this pass

A single inline pure-function probe passed these focused checks:

1. Jun name normalization plus rejection of an invented name.
2. Conditional record contents under executed and suppressed ration actions.
3. Transitive deletion from the ration observation to the conditional record.
4. Rule speech learning for speaker/witness, targeted deletion, and replay.
5. Explicitly attributed fragment speech learning, deletion, and replay.

The coordinator owns the full backend/browser reruns and real-model evaluation.

## Revised assessment

**The three original review findings are resolved. No remaining important issue was established within the focused fixes.** The new conditional account implementation is consistent with the inspected action/suppression/deletion cases.

**Code-review verdict: ready for completion after the coordinator's final verification.** This verdict covers implementation correctness in the reviewed scope, not dialogue naturalness or semantic model quality. The separately reported real-model failures remain a product-quality limitation until evaluated and resolved or accurately documented.

---

# Narrow re-review: request-scoped source aliases — 2026-09-15

Reviewed `evidence_reference_map`, `resolve_output_sources`, `context_output_check`, prompt ID rendering, direct/`ask_npc` conversion before storage, and the added source-alias regression tests. No source edits or database/browser/model calls.

**Finding: no important defect established in this change.**

- Prompt rendering, output validation, and canonical resolution derive from the same filtered knowledge and `visible_memories` list. Deleted memories and unavailable-character entries do not enter the alias map.
- Rendering reverses that map rather than separately renumbering the prompt's grouped sections, so grouping own actions after other memories does not change the source meaning of `m1`, `m2`, etc.
- Direct responses resolve aliases before appending the new player exchange. Target responses in `ask_npc` resolve against the target's unchanged memory before storage.
- The initiating tool's `statement_id` is resolved against the asker's context before `_run_ask_npc`. It is therefore already canonical when historical speech is checked; the target's separate aliases cannot reinterpret it.
- Existing canonical references remain accepted only when their sources are visible. Newly stored dependency IDs are canonical, so later deletion still reaches derived replies.
- The existing loop lock keeps rendering, validation, conversion, and storage in one serialized day operation. A committed UUID retry returns the stored response without regenerating/reinterpreting aliases.
- The new memory-gap notice discloses no deleted content. The added hearsay example remains explicitly separated from actual day history by the prompt's examples instruction.

The added tests cover alias rendering, canonical dependency restoration, tool statement resolution, deletion of a derived reply, and rejection of an unavailable alias. The coordinator reported 23 focused checks passing; this reviewer did not duplicate that run. Model interpretation of the new example/notice remains part of the separate semantic evaluation.
