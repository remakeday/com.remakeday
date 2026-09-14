# Gameplay implementation plan

Spec: docs/superpowers/specs/2026-09-10-gameplay-design.md
User approved implementation in the current workspace. No Git metadata; baseline snapshot /tmp/pigfarm-gameplay-before-20260910. No migrations unless indispensable, no new dependencies. Preserve last turn night/advisor improvements.

## Task 1: Frontend clarity and reading (delegated)
Files: frontend/components/screens/{EntryScreen,MorningScreen,DayScreen,NightScreen,GodScreen}.tsx, relevant shared reading components, frontend/app/globals.css, frontend/tests.
- [x] Test tutorial visible before first play, numeric rules, day-specific budget, one-conversation-per-scene controls, free next scene, explicit notebook notification and refusal, unchanged night restoration.
- [x] Add small reusable help UI with initial entry presentation and optional reopen. Avoid blocking each repeat day; display current budget directly.
- [x] Apply damageClass only to image layers. Set dialogue/inputs/notebook body18px and supporting text16px with readable line-height; preserve focus traps and390px layout.
- [x] Update existing headless mock browser expectations for label changes. Run TypeScript and report exact checks; parent owns browser execution/server lifecycle.

## Task 2: Authored scene dialogue
Files: backend/apps/engine/app/dtos/scenario_dto.py, apps/scenarios/scenario_a/adapter.py, engine/app/use_cases/loop_interactor.py and scene_execution.py, tests/pure and tests/engine.
- [x] Failing regression: advance to scene2 yields real authored conversation with correct speakers, no generic record chatter and no ambient model call. Suppressed actions/missing actors don't produce contradictory hints.
- [x] Scenario data supplies dialogue with explicit actor/action prerequisites and dialogue source scope. Core selects eligible scene dialogue deterministically; persist utterances/notes and NPC memory using existing paths.
- [x] Distinguish action narration from dialogue; retain public source links. Test all6scenes and changed-rule days.

## Task 3: Preserve question-triggered rule intent
Files: engine/app/use_cases/intervention_interactor.py, loop_interactor.py, rule helper module, scenario DTO/data as needed; tests for previews/application/utterances.
- [x] Failing integration regression: original user rule previews preserving report subject and question trigger, confirm persists semantics; no automatic scene execution; matching question activates, unrelated question doesn't.
- [x] Store canonical finite question-triggered action semantics in existing action field to avoid DB migration. Validate original meaning; decline extra unsupported constraints. Select authored conditional replies from character knowledge only after their actual scene-action prerequisites. Keep ordinary direct questions on the NPC model. Record actual opportunity/result with the spoken source ID.
- [x] Keep regular scene rules working and prevent question rules entering autonomous planner actions. Actual reply cannot invent a completed report from recording/approaching alone.

## Task 4: Verification and activation
- [x] Focused red/green tests and full backend suite on pigfarm_test, architecture4contracts, TypeScript.
- [x] Headless mocked frontend: tutorial to day, six-scene labels, mobile typography/image-onlydamage, notes and night, 5dayflow. Only one browser owner; finallyclose.
- [x] Small real NPC model sample checks in-character response and conditional report questions using fake repositories, no player sessions. Review whole change, resolve findings.
- [x] Update API contract/verification notes; restart only owned backend and verify /health and /play. Report model quality limitations accurately.

## Decisions and progress
- Ruling: work in supplied checkout with snapshot since no Git repository exists. No commit/worktree operations.

- Ruling: real NPC samples invented report contents despite prompt changes, so conditional report responses use authored story branches instead of free generation. This follows the approved authored-core/AI-interaction direction and removes the model call for this action.
- Ruling: actor knowledge may reveal private report content after a completed authored visit, while that dialogue remains reported speech to the player. Player-visible records are not the entirety of actor knowledge.
- Review: fixed report/look-at homonym false triggers and reporter-subject reversal; scoped review passed45puretests and48scene/action combinations.
- Verification: backend386tests; frontend4headlesssuites; TypeScript; architecture4contracts. Evidence docs/review-verification/2026-09-10-gameplay/README.md.
