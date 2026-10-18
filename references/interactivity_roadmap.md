# Interactivity roadmap — what is in, what is out, and why

Decision record for the interactivity work. Written after reviewing iSpring Visuals / QuizMaker /
TalkMaster / Suite as reference points. Read this before proposing "let's add type X" — the answer may
already be here, with a reason.

## Guiding decisions

1. **iSpring parity is not a goal.** iSpring ships 14 interaction templates and 14 question types, but
   most of its templates are *presentation* widgets (tabs, accordion, carousel, catalog, FAQ,
   glossary) that this engine already covers. Copy the pedagogical intent, not the inventory.
2. **Interactions are formative; `quiz` stays the only summative gate.** Certificate, attempt limit and
   Sheets sync keep working exactly as they do today.
3. **WCAG 2.2 AA survives.** Keyboard path is a definition-of-done item, not a follow-up task.
4. **Complexity budget: 22 slide types maximum.** Today: 18. Each new type costs a schema branch, a
   renderer, a docs section, a gate entry and a Playwright test. One in, one out after the cap.
5. **No new engine dependency.** Single-file, client-side, no persistence, no CDN beyond what ships
   today (Tailwind, fonts, confetti, icons).

## Phases

| Phase | Scope | Why this order | Status |
|---|---|---|---|
| **0** | Interactivity Map, placement doctrine (`references/interactivity_patterns.md`), validator density analytics | Cheapest, highest leverage: changes what the agent *decides* before writing content | done |
| **1** | Question types `multipleResponse`, `ordering`, `matching`, `numeric` + the `checkpoint` block (formative, any slide) | Assessment quality first: procedure knowledge needs ordering/matching, not another MCQ | done |
| **2** | `hotspotImage` (covers labeled graphic + guided image + hotspot question) | Highest gap-per-line: three iSpring templates in one renderer, reuses the image/hotspot primitives | done |
| **3** | `branchingScenario` (TalkMaster-style conversation/decision tree) | Biggest engagement win for SOP judgement + soft skills; pure state machine | done |
| **4** | `dragDropSet` (sort / categorize / order) | Most expensive: no drag infrastructure existed; solved by making click-to-place primary and layering HTML5 drag on top | done |

> `checkpoint` shipped as an **in-slide block**, not a slide type: it works on any of the 19 types,
> keeps the schema's slide-type contract stable, and turns a passive slide into an active one without
> adding a renderer. The validator counts it as an active moment.
>
> `branchingScenario` shipped as a node graph with per-choice feedback, endings, debrief and
> restart. It is the `scenarioPicker` upgrade, not a replacement: one decision stays a
> `scenarioPicker`, a conversation with consequences becomes a `branchingScenario`.
>
> `hotspotImage` shipped with two modes in one renderer: `explore` (labeled graphic / guided tour) and
> `find` (locate the target among decoys). Both are keyboard-operable pins over a percentage-positioned
> image, so one renderer covers three iSpring templates without drag mechanics.

All four phases are shipped. Any further interaction type needs a fresh decision: see the
acceptance criteria below and the complexity budget of 22 slide types.

## Deliberately out of scope

| iSpring capability | Why not |
|---|---|
| Webcam / microphone recording (`getUserMedia`) | Permissions, device variance, storage; breaks single-file and needs a server for anything useful |
| Screen capture / screencast | Same as above, plus file size |
| PowerPoint import | This engine authors from JSON; there is no slide source to import |
| Stock content library, character avatars, animated actors | Licensing + megabytes; the design system is deliberate about its visual language |
| Video/audio editor | Out of scope for a module builder |
| Equation editor | Rare in SOP/corporate training; a `fillIn` or image covers it |
| Per-question timer, timed exam mode | Conflicts with the in-memory/no-persistence model (a reload would reset the clock) |
| Question groups + random N per group | Cheap to add later; the current shuffle already defeats answer-sharing |
| Partial credit / penalties | Would change the scoring model, the webhook payload and the pass logic. Only add if a user asks |

## Acceptance criteria for any new interactive type

1. Schema branch with required fields, and `additionalProperties: false`.
2. Renderer registered in `SLIDE_RENDERERS`; `tools/verify_module.py` passes (it enforces registry ↔
   schema parity).
3. Keyboard path + a text alternative for anything visual; `aria-live` for feedback.
4. Formative only — no writes to `quizScore`, `quizAttemptCount`, or the webhook payload.
5. Playwright coverage in `scripts/smoke_test_module.py`: render, one correct interaction, one wrong
   interaction, and the feedback text.
6. A section in `references/slide_types.md`, an entry in the slide-type tables here and in
   `references/interactivity_patterns.md`, and a line in `SKILL.md`.
7. `scripts/self_check.py` still green; the sample in `assets/sample.content.json` exercises the new
   type so every future run covers it.
