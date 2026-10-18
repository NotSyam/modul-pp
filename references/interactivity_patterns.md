# Interactivity patterns — where interaction earns its place

Interactivity in this engine is a **teaching device**, not a decoration. The default output of
AI-generated e-learning is a wall of cards with a quiz bolted on the end; that is a presentation, not
a course. This page exists so the agent decides *deliberately* where a learner should act, and stays
honest about where they should just read.

Applies to every module built with `modul-pp`. Read it in Step 3.5 of `SKILL.md`, before writing
`content.json`.

---

## 1. The one test that matters

**The delete test:** delete the interaction from the slide. If the learner's understanding is the
same, the interaction was decoration — delete it in the real build too.

Corollary: **an interaction must have a consequence.** A click that reveals text the learner could
have read anyway is a tab, not an interaction. A consequence means feedback, a state change, a
branch, or progress that is earned.

## 2. Three classes of slide

| Class | Learner does | Slide types | Effect on memory |
|---|---|---|---|
| **Passive** | reads / watches | `cover`, `cardList`, `kpiDashboard`, `riskCards`, `stepByStep`, `comparisonTable`, `calloutBox`, `summaryCertificate` | weak — recognition only |
| **Semi** | browses, opens, reveals | `tabbedAccordion`, `faqAccordion`, `twoCardAccordion`, `docTabs`, `imageGallery`, `videoEmbed`, `verificationMatrix` | weak — orientation, good for reference material |
| **Active** | decides, answers, sequences, explores with feedback | `quiz`, `scenarioPicker`, `treeCanvas` (hotspot + role filter), `hotspotImage`, `branchingScenario`, `dragDropSet`, **or any slide with a `checkpoint` block** | strong — retrieval / application |

The canonical classification lives in `scripts/validate_content.py`
(`ACTIVE_TYPES` / `SEMI_TYPES` / `PASSIVE_TYPES`) because the validator reports density from it;
`scripts/self_check.py` fails when a schema slide type is missing from those sets. Keep this table and
the code in step.

Semi-active is *legitimate* for reference material (a form list, a glossary, a policy table). Do not
dress a reference table up as an active slide, and do not turn a procedure into an accordion.

## 3. Interaction patterns

Pick the pattern from **what the learner must be able to do**, not from what looks impressive.

| # | Pattern | Learner does | Use when content is… | Implement with | Feedback required |
|---|---|---|---|---|---|
| 1 | **Recall** | produces the answer from memory | definitions, thresholds, clause numbers | `checkpoint` block, `quiz` (`fillIn`, `mcq`) | yes — explanation, not just "wrong" |
| 2 | **Recognize** | picks the correct option among plausible ones | rules with near-miss exceptions | `checkpoint` block, `quiz` (`mcq`, `multipleResponse`) | yes |
| 3 | **Sequence** | puts steps in the right order | procedures, approval flows | `checkpoint` block or `quiz` (`ordering`) | yes — show correct order |
| 4 | **Match** | pairs items across two columns | role → responsibility, form → purpose | `quiz` (`matching`) | yes |
| 5 | **Categorize** | sorts items into buckets | risk classes, document types | `dragDropSet` | yes — per bucket |
| 6 | **Decide** | chooses under a constraint and sees the consequence | SOP judgement calls, escalation, ethics | `scenarioPicker` (one step), `branchingScenario` (tree) | yes — consequence + debrief |
| 7 | **Explore** | inspects a diagram/photo for hotspots | layouts, equipment, org charts, document anatomy | `hotspotImage` (`explore` = guided tour, `find` = locate the target), `treeCanvas` | light — found/total progress |
| 8 | **Reflect** | commits to an answer *before* seeing the explanation | myths, common misconceptions | `checkpoint` block placed before the explanation card | yes — contrast their guess vs truth |

Patterns 1–4 and 6 are *retrieval*; 5 and 7 are *manipulation*; 8 is *metacognition*. A module with
only pattern 1 is a quiz. A module with only 7 is a poster with pins.

## 4. Placement rules

1. **No interaction in the first two slides.** The cover teaches nothing and an early graded item
   punishes the learner for not having read yet. (Existing modules start with `cover` + an overview —
   keep it that way.)
2. **One active slide per 3–4 content slides, minimum 20% of the module.** Below that the module is a
   reading assignment; above ~50% the learner never gets enough input to act on.
3. **Never let more than 5 consecutive passive/semi slides pass** without an active moment. That is
   where attention dies. A `checkpoint` is the cheapest fix.
4. **Interactions are formative by default.** They carry feedback, not marks. The `quiz` slide is the
   only summative gate (pass → certificate + webhook). Do not scatter scored items across the module
   unless the user asks for it.
5. **Never make compliance-critical text interactive-only.** Mandatory wording (SOP clauses,
   disclaimers, legal text) must be fully readable without clicking. Interactive elements may *add*
   practice on top of it, never replace it.
6. **Place the interaction immediately after the content it tests**, not in a block at the end.
   Retrieval works when it is close to encoding.
7. **Every active slide must have a keyboard path** and a text alternative for anything image-based.
   WCAG 2.2 AA is claimed for this engine; an interaction that only works with a mouse breaks that
   claim.
8. **Distractors must be plausible misconceptions**, not obvious throwaways ("ignore the rules"). A
   learner who has never read the material must not be able to pass by elimination.
9. **Cap the effort per interaction.** If a drag-and-drop task takes more than ~60 seconds of motor
   precision, it is testing dexterity, not knowledge. Prefer 4–6 items.
10. **Say why it was placed.** Every active slide gets one line in the Interactivity Map
    ("why here") so a reviewer can challenge it.

## 5. Interactivity Map (produce this before building)

Before writing `content.json`, output this table and get the user's sign-off. It is the "breakdown of
which parts can take interactivity" that this engine asks for. One row per slide.

| Slide | Title | Content kind | Class | Pattern | Implementation | Why here | Effort |
|---|---|---|---|---|---|---|---|
| 0 | Pendahuluan | intro | passive | — | `cover` | — | — |
| 7 | Ketentuan Umum 6.1–6.3 | rules | semi | — | `tabbedAccordion` | reference, must stay readable | — |
| 10 | Alur persetujuan | procedure | active | sequence | `quiz` ordering | urutan sering tertukar di lapangan | S |
| 12 | Penilaian risiko | judgement | active | decide | `scenarioPicker` | risiko tinggi kalau salah eskalasi | M |
| 14 | Daftar formulir | reference | semi | — | `docTabs` | lookup table, bukan skill | — |

Rules for the map itself:
- Mark at least one slide as `passive` **and justify it**. A map where everything is active is a map
  that was not thought about.
- `Effort`: S (≤30 min authoring) / M (30–90) / L (>90, needs media or a new renderer).
- If a row needs a slide type the engine does not have, say so and propose the closest pattern —
  do not silently invent one.
- After the build, `scripts/validate_content.py` prints the actual density; if it disagrees with the
  map, the map was optimistic — fix the content, not the numbers.

## 6. Anti-patterns (each has been seen in real builds)

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| **Click-to-reveal everywhere** | 30 clicks, zero retrieval | keep reveal for 1–2 myth-busting slides max |
| **Quiz-only interactivity** | assessment crammed at the end, no practice | add 1–2 `checkpoint`s mid-module |
| **Fake decision** ("pilih mana yang benar?" with one sane option) | learner spots the answer without reading | make distractors plausible, tie to a real near-miss |
| **Mega drag-and-drop** (12 items, 3 buckets) | fatigue + a11y nightmare | 4–6 items, one screen |
| **Interaction as navigation** (must click all tabs to continue) | busywork disguised as engagement | no forced click-through; gate on time, not clicks |
| **No feedback** ("Salah. Lanjut.") | learner learns nothing from the error | explain *why* the chosen option is wrong |
| **Scored everything** | learner optimises for points, not understanding | formative interactions + one summative quiz |

## 7. How this plugs into the engine

- **Formative vs summative.** `quiz` is summative: `state.quizCompleted`, `quizScore`, 5-attempt
  limit, certificate unlock, webhook sync. `checkpoint` and the other active types are formative:
  feedback + local completion only, they never touch the score, the attempt counter, or the sheet.
- **Slide gate.** The 10-second gate timer is about time on slide, not correctness. A `checkpoint`
  *may* call `completeCurrentSlideTask()` to release the gate early once answered correctly, but it
  must never hard-block navigation (that turns a practice item into a locked door).
- **No persistence.** Interaction state is in memory like everything else; a reload resets it. That is
  intentional and documented in `references/engine_behaviour.md`.
- **Authoring cost is real.** Each active type needs a schema branch, a renderer, a docs section, and a
  Playwright test. Adding one is a deliberate decision, not a whim — see
  `references/interactivity_roadmap.md` for what is in and out of scope.
