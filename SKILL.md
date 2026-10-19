---
name: modul-pp
description: Transform raw training documents, SOPs, syllabi, or slide breakdowns into production-ready, self-contained interactive e-learning modules (single HTML file) with 21 slide types, slide gate timers, anti-spam quiz evaluations, Google Sheets sync, and certificate printing. Use when the user asks to build an interactive e-learning module, or types /modul-pp (aliases /modul, /elearning).
---

# Modul PP — Interactive E-Learning Module Builder Skill (/modul-pp)

Build production-ready, self-contained interactive e-learning modules (single HTML file) from a
slide-by-slide content breakdown + optional reference documents.

## What this skill produces

A **single `.html` file** that runs in any modern browser (open via `file://`, no server needed),
roughly 250–280 KB. Each module includes:

- Top player bar (logo, course code, effective date, Terminologi / Tenggat / Petunjuk modals, theme
  toggle, fullscreen) + collapsible off-canvas mobile sidebar (Menu / Transkrip / Lampiran) with a
  centred 16:9 stage viewport and bottom playbar (play/pause, replay, timecode, seekbar, CC toggle,
  speed, slide counter, prev/next) + caption dock
- Per-slide audio narration (`./audio/unit_<N>.mp3` or a 45-second fallback simulator)
- 21 slide types: `cover`, `cardList`, `treeCanvas`, `scenarioPicker`, `tabbedAccordion`,
  `verificationMatrix`, `twoCardAccordion`, `docTabs`, `kpiDashboard`, `riskCards`, `quiz`,
  `summaryCertificate`, `imageGallery`, `videoEmbed`, `calloutBox`, `stepByStep`,
  `comparisonTable`, `faqAccordion`, `hotspotImage`, `branchingScenario`, `dragDropSet`
- Dark/light theme toggle (default dark, configurable via `course.defaultDark: false`) — 4 brand presets (`ptpp`, `corporate`, `education`,
  `tech-startup`) + a custom inline palette
- **Self-contained logo**: a `logo.png` next to `content.json` is inlined automatically (plus an
  optional `logo-dark.png` for dark mode, and a monogram badge when no file exists)
- **Balanced card grids**: an odd number of cards centres the last row instead of leaving a hole
- Quiz: **7 question types** (MCQ, True/False, Fill-in, multiple-response, ordering, matching,
  numeric), shuffled options, one question per screen, identity card, attempt limit, post-submit
  review — plus an optional **formative `checkpoint`** block on any slide (ungraded practice that
  releases the slide gate)
- Slide gate timer, Google Sheets webhook sync, SCORM runtime, printable A4 certificate (built-in or
  custom template), pan/zoom tree canvas with role filter + hotspot modal
- Tactile Web Audio tones, Canvas confetti, WCAG 2.2 AA keyboard nav + ARIA roles

## Skill architecture

```
modul-pp/
├── SKILL.md                     ← you are here (workflow + rules)
├── README.md                    ← human-facing documentation
├── assets/
│   ├── shell.template.html      ← the canonical engine (edit directly, then run the gates)
│   ├── content.schema.json      ← JSON Schema for content.json
│   ├── brand.profiles.json      ← 4 brand presets
│   ├── certificate.template.example.html  ← starting point for a custom certificate
│   ├── sample.content.json      ← 21-slide example covering every slide type
│   ├── sample.slide_breakdown.md
│   └── project-runner/          ← portable per-project build script
├── scripts/     build_module.py, validate_content.py, generate_audio.py, package_scorm.py,
│                smoke_test_module.py, self_check.py
├── references/  engine_behaviour.md, interactivity_patterns.md, interactivity_roadmap.md,
│                slide_types.md, input_format.md, brand_profiles.md,
│                pedagogical_patterns.md, gas_webhook_setup.md
├── tools/       verify_module.py, sync_installs.py
├── dsh-command/ DSH slash-command plugin (/modul-pp) — separate optional package
└── upstream/    index_tree_canvas.html (pinned design reference — read-only)
```

Repo scaffolding (`.gitignore`, `LICENSE`) and local artifacts (`build/`, `test_build.html`) also
exist; they are not part of the skill interface.

- **`assets/shell.template.html` is the canonical engine.** It is directly maintained, NOT generated.
  `scripts/build_shell_template.py` no longer exists and must not be recreated: the shipped shell had
  drifted 617 lines ahead of the old generator, and running it silently destroys the gate timer,
  SCORM runtime, participant-identity card, attempt limit and Sheets webhook. Edit the shell
  directly, then **always** run `scripts/self_check.py`.
- **`upstream/index_tree_canvas.html` is the pinned design reference** (the finished PT PP SOP
  module). Keep it read-only; the shell's visual language must stay faithful to it.
- **`dsh-command/` is an optional companion package, not part of the skill.** A DSH skill can only
  contribute a `name` and a `description` to the agent catalog, so the `/modul-pp` command lives in
  `dsh-command/` as a separate DSH command plugin. The skill works fine without it.

## Workflow (always follow these steps)

### Step 1 — Read the user's slide breakdown + reference docs

The user provides a slide-by-slide breakdown in **structured bullets** format (canonical spec in
`references/input_format.md`), optionally with reference docs (PDF, DOCX, MD, TXT) — read them to
enrich the content.

If the user provides prose instead, extract the structure: Slide N → `slides[N].type` → fields per
the schema. When unclear which slide type fits, consult `references/slide_types.md` for the taxonomy
+ decision tree.

### Step 2 — Pick the brand profile and confirm certificate identity

**Default to `ptpp`** — the only preset carrying the reference module's exact palette, so the only
one that satisfies UI parity. `build_module.py` also defaults to `ptpp` when `content.json` has no
`brand` block.

- Indonesian state-owned enterprise / infrastructure → `ptpp` (default)
- Generic corporate training → `corporate` (departs from reference parity)
- School / academic / continuing education → `education` (departs)
- Tech startup / engineering playbook → `tech-startup` (departs)
- Full colour control → `custom` (all inline fields required)

If the context suggests a non-`ptpp` preset, confirm explicitly and state that the visual identity
will differ from the reference module.

**Also confirm the certificate identity fields before building**: `brand.orgName`, `orgDivision`,
`signatory`, `certTitle`, `certRegPrefix` (or `course.certificate.labels`). The `ptpp` preset signs
certificates as "SVP - Operation Control & SCC" with a PT PP registration prefix — wrong for any
other organisation, and the learner only discovers it on the printed PDF.

### Step 3 — Interactivity Map, then `content.json`

**First produce an Interactivity Map and get sign-off on it**: one row per slide with its class
(passive / semi / active), the interaction pattern, the implementation type, why the interaction sits
there, and the authoring effort. The table template, the eight patterns, the placement rules and the
anti-pattern list live in `references/interactivity_patterns.md` — read it before choosing slide
types. Read `references/interactivity_roadmap.md` when the user asks for an interaction type that does
not exist yet: it records what is in scope, what is deliberately out, and why.

Two failure modes this step exists to prevent: a module that is 18 `cardList` slides plus a quiz at the
end (a presentation, not a course), and a module where every slide demands a click (no time left to
learn). Aim for one active slide per 3–4 content slides, at least 20% of the module, and justify every
`passive` slide in the map.

Then construct the JSON following `assets/content.schema.json`. Key rules:

1. **`units[]` and `slides[]` MUST have the same length** — `units[N]` is the sidebar entry for
   `slides[N]`.
2. **Each `slide.type`** must be one of the 21 supported types. Per-type required fields are in
   `references/slide_types.md`.
3. **Rich text**: fields `desc`, `lead`, `body`, `note`, `a` natively support Safe HTML
   (`<strong>`, `<em>`, `<br>`, `<code>`, `<span>`) and Markdown (`**bold**`, `*italic*`, `\n`).
   Do not escape HTML tags manually. Literal hex codes written in copy are preserved verbatim.
4. **Narration**: put the verbatim audio script in `slides[N].narration` **or** in the top-level
   `narration: {"0": "...", "1": "..."}` object. Per-slide wins. It drives the Transkrip tab, the CC
   caption dock, and the TTS generator; slides without one get an auto-composed "intisari" script and
   an empty caption dock.
5. **`glossary`, `tenggatCheatSheet`, `hintTips`, `resources`** are optional — omit when unused.
   Cheat-sheet cards render left-aligned with a value pill; `"wide": true` spans both grid columns.
6. **`brand` block**: either `{"preset": "name"}` or `{"preset": "custom", ...inline fields}`.
7. **`course.certificate`** (optional) customises the printed certificate: `template`, `pageSize`,
   `printPadding`, `labels`, `dateLocale`, `regNumberFormat`. See "Custom certificate PDF" below.
8. **Logo is automatic.** Drop `logo.png` (or `.jpg`/`.svg`/`.webp`) next to `content.json` — the build
   inlines it as a data URI, so no `course.logo` and no separate asset folder are needed. Add
   `logo-dark.png` for a real dark-mode asset; without it the single logo is rendered as a white
   silhouette in dark mode. With no file at all, the header shows a monogram badge from the brand name
   instead of a broken image. `--logo` / `--logo-dark` override detection.

### Step 4 — Save `content.json`

Save to `<project-dir>/content.json` (keep the skill directory clean).

### Step 5 — Validate `content.json`

```bash
python3 <skill-root>/scripts/validate_content.py <content.json>
```

Must exit `0` and print `✓ Valid!`. The validator has **zero third-party dependencies** (it uses
`jsonschema` when installed, otherwise a built-in validator for the subset the schema uses).

It also re-validates each slide against its own type definition, so a wrong field or a typo like
`comparisonTabel` produces a precise message with a suggestion instead of "matches 0 of 21 schemas",
and prints semantic advisories (out-of-range `correctIndex`, duplicate question ids, narration
coverage, missing certificate template, `units[].duration` not MM:SS, …). Advisories do not fail the
build — add `--strict` when you want them to.

Every run also prints an **interactivity line** and warns when the placement rules in
`references/interactivity_patterns.md` are broken:

```
Interaktivitas: 3/18 aktif (17%) · 6 semi · 8 pasif · pedoman ≥20%
! kepadatan interaksi 16.7% (3/18) — di bawah pedoman 20%.
! 12 slide non-aktif berurutan (slide 4–15). Pedoman: maksimal 5.
! tidak ada slide 'quiz': ... sertifikat tidak akan pernah terbuka ...
```

If these fire, fix the content (add a `checkpoint`, split a long passive stretch, add the quiz slide) —
do not lower the guidance. Note that `--quiet` suppresses the line but not the warnings.

### Step 6 — Generate audio narration (optional)

```bash
python3 <skill-root>/scripts/generate_audio.py \
  --content <content.json> \
  --output-dir <project-dir>/audio \
  --voice ardi --rate -4%
```

Voices: `gadis` (default), `ardi`, `jenny`, `guy`, or any full Edge-TTS voice name. The script
resolves narration per slide (`slides[N].narration` → `narration[N]` → auto "intisari" fallback),
applies a pronunciation dictionary for SOP/ISO/LMS/BUMN/PT PP-style jargon, and strips Safe HTML
before synthesis. Useful flags: `--check` (coverage report, no TTS), `--dry-run` (print the exact
script), `--unit N`, `--force`, `--no-phonetic`, `--pronunciation-file extra.json`. Requires
`pip install edge-tts`.

### Step 7 — Build module HTML

```bash
python3 <skill-root>/scripts/build_module.py \
  --content <content.json> \
  --output <project-dir>/index.html \
  --validate
```

`build_module.py` runs four order-sensitive steps: (1) brand palette, (2) build placeholders,
(3) certificate template, (4) inject `COURSE`. The order matters — running the palette or placeholder
pass after injection would silently rewrite hex codes and `__TOKEN__` strings the author wrote inside
slide copy. It fails hard on unfilled placeholders and prints a contrast advisory for brand tokens
that cannot carry white text at 4.5:1.

### Step 8 — Run the verification gate

```bash
python3 <skill-root>/tools/verify_module.py <project-dir>/index.html --content <project-dir>/content.json
```

**Must pass before reporting success.** `tools/verify_module.py` is an offline gate (needs Node.js on
PATH, no browser). It checks static DOM tag balance, JS syntax of every `<script>` block via
`node --check`, required DOM ids (attribute-order tolerant), stray `>` text nodes, that every
`SLIDE_RENDERERS` entry is defined **and covers exactly the schema's slide types**, that `COURSE` was
actually injected, that no build placeholder survived, that the certificate contract ids exist, and —
with `--content` — that the injected `COURSE` literal matches `content.json` byte for byte, which
catches a stale HTML. Native `alert()`/`confirm()` usage is reported as an advisory.

Exit `0` = clean.

### Step 9 — Smoke test (optional but recommended)

```bash
python3 <skill-root>/scripts/smoke_test_module.py <project-dir>/index.html
```

Loads the module in headless Chromium, walks **every** slide through its renderer (no hardcoded
sample indices), and checks navigation, the quiz container and identity-card toggle, the tree canvas
layout, the certificate contract, `printCertificate()` and the modals. Requires
`pip install playwright && playwright install chromium`.

Expected non-fatal warnings:
- `cdn.tailwindcss.com should not be used in production` — cosmetic, expected for single-file distribution.
- `AudioContext was not allowed to start` — browser autoplay policy; resumes on first user interaction.
- `Failed to load resource: ERR_FILE_NOT_FOUND` — missing `assets/logo.png` or `audio/unit_N.mp3` when the user has not supplied them.

### Step 10 — Run the skill's own regression gate (after any shell edit)

```bash
python3 <skill-root>/scripts/self_check.py
```

Runs 14 checks against the shipped sample: schema validation, build, verification gate with COURSE
parity, palette-collision regression, author hex-literal preservation, placeholder contract, custom
certificate template, narration pipeline (including phonetic respelling), and regenerating +
verifying the committed `test_build.html`. Add `--with-smoke` to include Playwright. **Run this
whenever you edit `assets/shell.template.html` or any script**, before touching a real project.

### Step 11 — Report to the user

- The final HTML file path
- Brand preset used (and, for non-`ptpp`, that it departs from the reference UI)
- Number of slides + a quick type breakdown
- Verification-gate results and any non-fatal warnings to ignore
- Which certificate identity/labels were used, and whether a custom template was applied
- Next steps: attach real logo + audio files, iterate by editing `content.json` and re-running
  `build_module.py`

## Custom certificate PDF

The certificate is printed through the browser (`window.print()` → "Save as PDF"), driven by the
`@media print` rules in the shell. Three levels of customisation:

1. **Built-in layout, different text/geometry** — set `course.certificate`:

```json
"course": {
  "certificate": {
    "pageSize": "A4 portrait",
    "printPadding": "10mm",
    "dateLocale": "en-GB",
    "regNumberFormat": "CERT/{year}/{seq}",
    "labels": {
      "kicker": "CERTIFICATE OF COMPLETION",
      "presentedTo": "This certificate is awarded to:",
      "passNote": "has completed the module and <strong>PASSED THE ASSESSMENT</strong>",
      "scoreLabel": "Score",
      "passThresholdNote": "Passing threshold {passingScore}%",
      "dateLabel": "Date of Completion:",
      "footerNote": "Corporate Learning Platform"
    }
  }
}
```

2. **Your own design** — point `course.certificate.template` at an HTML fragment that replaces the
   inner markup of `#certificatePrintArea`. Start from `assets/certificate.template.example.html`.
   Use `{{token}}` for build-time values (course/organisation/signatory names, labels, brand colours)
   and keep the five contract DOM ids (`certRecipientName`, `certRecipientNIP`, `certScoreVal`,
   `certDateVal`, `certNumberLabel`) — the engine fills those at print time. An unknown `{{token}}`
   fails the build; a missing contract id fails the verification gate.

3. **Edge-to-edge / print-shop design** — `printPadding: "0"` plus `pageWidthMm`/`pageHeightMm` for a
   non-standard page, and paint your own borders in the template.

Two ready starting points ship with the skill: `assets/certificate.template.example.html` (portrait
award card) and `assets/certificate.template.modern.html` (landscape, full-bleed navy sidebar).

**Preview without passing the quiz:** open the built module with `#cert-preview` appended to the URL
(`file:///.../index.html#cert-preview`). The engine fills sample participant data, reveals the
certificate at true page size over the player, and shows a dismissible badge — press `Ctrl+P` to see
exactly what will print. This is the fastest design loop: edit the template → rebuild → refresh with
`#cert-preview`.

The registration number is deterministic (NIP + course code + year), so reprinting yields the same
number. Full runtime detail: `references/engine_behaviour.md`.

## UI parity with the reference module

Generated modules must visually match the design system of `upstream/index_tree_canvas.html`. This is
a first-class requirement, not a nice-to-have. Non-negotiables:

- **Palette — strict blue/white corporate.** primary `#2B73BD`, primaryHover `#205c99`, secondary
  `#5A89B8`, secondaryLight `#7eabd9`, accent lightBlue `#38BDF8`, light canvas iceBg `#F0F4F7`,
  surface white, dark canvas `#09111E`, dark surface `#111C2E`, dark border `#1F2F4A`, dark subtle
  `#16233B`. **No brown/beige/tan accents.**
- **Fonts**: Plus Jakarta Sans (sans), JetBrains Mono (mono). Default theme is **dark**
  (`darkMode: 'class'`).
- **Player chrome anatomy**: top player bar → collapsible off-canvas mobile sidebar with tabs
  Menu / Transkrip / Lampiran → centred stage viewport → bottom playbar → caption dock.
- **Interactive touch targets must be ≥44px.**
- **Never combine `line-clamp-*` with `overflow-y-auto`** (the clamp fights the scroll container).
- **Chevrons inside `<summary>` need `shrink-0`** so they do not collapse.
- **The logo appears ONLY in `#topHeader`**, uses the transparent PNG, and is styled
  `dark:brightness-0 dark:invert`.

### Blueprint visual language (do not flatten this)

The module reads as an *institutional engineering terminal* — structured, precise, like a
civil-engineering blueprint. This is deliberately NOT a generic rounded-card SaaS dashboard:

- **Hero / cover card** uses a **three-stop** gradient `bg-gradient-to-br from-brand-primary
  via-[#1F548E] to-[#163D6B]` with `shadow-xl border border-white/10` — never a flat two-stop gradient.
- The hero carries an **architectural grid watermark**: `absolute inset-0 pointer-events-none
  opacity-10 bg-[radial-gradient(#ffffff_1px,transparent_1px)] [background-size:16px_16px]`, with hero
  content on `relative z-10`.
- Hero metadata is a **frosted pill**: `inline-flex items-center gap-2 px-2.5 py-1 rounded-lg
  bg-white/15 backdrop-blur-sm text-xs font-semibold text-sky-100 border border-white/20`, including
  a `w-1.5 h-1.5 rounded-full bg-sky-300 animate-pulse` live dot.
- **`UI.card` is `rounded-xl`, not `rounded-2xl`**, with `border-slate-200/90 shadow-sm
  hover:border-brand-primary/40 transition-colors`. Uniform large radii flatten the hierarchy.
- **`UI.label` is sentence case** (`text-xs font-bold text-brand-primary … tracking-normal`) — no
  `uppercase tracking-wider`.
- **Tables**: wrap in `overflow-x-auto`; body uses `divide-y divide-slate-100`; rows get
  `hover:bg-slate-50/50 transition-colors`; the highlighted column gets
  `border-x border-brand-primary/10` and its header cell `border-x border-brand-primary/20`; cells
  are `align-top leading-relaxed`.
- **Numbered step lists**: the number chip is a *ghost* chip that fills on hover —
  `w-9 h-9 rounded-xl bg-brand-primary/10 border border-brand-primary/30 shadow-sm
  group-hover:bg-brand-primary group-hover:text-white transition-all` — and each step body is wrapped
  in `${UI.card} p-4`.

### Per-project runner

When the user wants a module folder they can rebuild without remembering CLI flags, copy
`assets/project-runner/build_module.py` next to their `content.json`. It auto-detects the skill root
(explicit flag → `MODUL_PP_SKILL_ROOT` → `.modul-pp.json` → a sibling `modul-pp` folder → common
install locations derived from the user's home directory — **never a hardcoded machine path**), then
runs validate → build → verify in one command. `--check` builds to a temporary file and verifies it
without touching `index.html`, so the check always tests the *current* `content.json`.

## Review and revision loop

Real module builds are iterative. Users run critique passes between builds and then ask for revisions:

1. **Build** the module with `build_module.py`.
2. **Critique** — if the user asks for a review (or a `/critique`-style pass, or names a design/
   instructional skill), audit against `references/pedagogical_patterns.md` and the UI-parity rules
   above. Cover cognitive load (are bureaucratic clause numbers like "Poin 6.1 s.d. 6.5" leaking into
   titles?), quiz rigour (are distractors realistic misconceptions, or lazy "ignore the rules"
   options?), and visual hierarchy (is every slide a same-radius card?).
3. **Revise** by editing `content.json` for content and `shell.template.html` only for engine/UI
   changes, then re-run the full gate (`validate` → `build` → `verify`) plus `scripts/self_check.py`
   if the shell changed.
4. **Re-narrate** with `generate_audio.py --force` after any narration text change — stale audio is a
   common miss. `--check` tells you which slides have narration at all.

**Content polish rule:** learner-facing titles must be thematic, not bureaucratic. Prefer
"Prinsip Parenting, Grading & Perjanjian" over "Ketentuan Umum (6.1 sampai 6.5)". If the user's
breakdown is a list of clause ranges, rewrite the titles during content authoring.

## Engine behaviour

The full runtime contract lives in `references/engine_behaviour.md`: gate timer, quiz attempts and
identity card, webhook sync condition and payload, SCORM, dev/review badge, certificate printing,
the learner-experience invariants, the audio narration contract, and the Apps Script receiver code.
Read it before answering "does the module do X?" and before editing the shell.

Two things worth knowing without opening that file:

- **Local progress persistence**: Slide progress, completed units, participant identity, and passed quiz state are safely persisted in `localStorage` keyed by `course.code` (with graceful fallback if sandboxed or unavailable). A page refresh resumes the learner at their current slide without losing completed gates. Quiz attempt count is kept per session to preserve fair retry limits.
- **Production Gating by Default**: `course.devMode` defaults to `false`. In production, gating countdown timers are strictly enforced and `#cert-preview` is locked. For draft review and testing, set `"devMode": true` to unlock slide hopping and certificate inspection.
- **Webhook sync fires on pass OR on the final failed attempt** (status `TIDAK LULUS (MAX ATTEMPT)`);
  intermediate failed attempts are not synced.

### Formative vs summative

Only the `quiz` slide is **summative**: it sets `quizScore`/`quizCompleted`, enforces the attempt
limit, unlocks the certificate and triggers the webhook. Every other interactive type
(`scenarioPicker`, `treeCanvas`, `hotspotImage`, a `checkpoint` block, and the planned
`branchingScenario` / `dragDropSet`) is **formative**: it gives feedback and local progress, and must
never write to the score, the attempt counter, or the webhook payload. Keep that boundary when adding
or editing renderers — it is what keeps "practice" safe to fail.

## Critical rules (the "why" matters)

1. **Always validate before building.** A malformed `content.json` renders a module that shows a red
   error instead of content.
2. **`assets/shell.template.html` is the canonical engine — edit it directly**, then re-run
   `scripts/self_check.py` and the verification gate. Never look for a shell generator.
3. **The `slides[]` array IS the slide order.** `units[]` follows the same order. There are no
   conditional slides: to render fewer slides, shorten both arrays.
4. **Each `slide.type` has a fixed set of expected fields.** Unknown fields are rejected by the
   validator and ignored by the renderer; missing required fields render empty sections.
5. **Quiz questions can be mixed** on one slide: `mcq`, `trueFalse`, `fillIn`, `multipleResponse`,
   `ordering`, `matching`, `numeric` — each discriminated by its own `type` field. The same seven
   types also work inside a `checkpoint` block, which is formative and never scored.
6. **Brand colour tokens are hex without `#`.** Write `"primary": "2B73BD"` — the build adds `#`.
7. **Audio files follow `./audio/unit_<slideIndex>.mp3`.** Absent files fall back to the 45-second
   simulator. Users can drop real MP3s next to the module at any time without rebuilding.
8. **The certificate only unlocks on quiz pass** (`state.quizCompleted &&
   state.quizScore >= COURSE.course.passingScore`).
   - **Quiz Bypass for QA/Testing**: To test certificate generation and course completion without taking the full quiz, set `"bypassQuiz": true` in `course` within `content.json`. Alternatively, setting `"devMode": true` reveals the `⚡ Bypass Kuis (Dev Testing)` button directly on the quiz slide. For instant print-to-PDF preview, append `#cert-preview` to the URL.
9. **The pass threshold is course-level** (`course.passingScore`, default 80). A `passingScore` inside
   a quiz slide is not supported and is rejected by the schema.
10. **Every interaction must earn its place.** Apply the delete test from
    `references/interactivity_patterns.md`: if removing the interaction leaves the learner's
    understanding unchanged, remove it. Interactions are formative; only the quiz is summative.
11. **Interactivity is placed by content type, not by mood.** Recall for thresholds and definitions,
    sequence for procedures, decide for judgement calls, explore for diagrams. An accordion labelled
    "interactive" is still a reading slide — do not count it as active in the Interactivity Map.
12. **No document numbering in learner-facing titles.** `validate_content.py` flags `Poin 6.1`,
    `Pasal 5`, `Lampiran III`, `s.d.` ranges and clause numbers like `6.1.2` in slide titles, tab
    labels and card titles. Rewrite them thematically while authoring, not afterwards — a learner
    should never have to decode the source document's structure to read a heading.
13. **Odd card counts are handled by the layout, not by padding the content.** Card grids centre the
    last row (`.cardgrid`); do not invent a filler card to make the count even.
14. **Pragmatic Variety Rule (Slide & Quiz Diversity)**: Apply interactive question types (`ordering`,
    `matching`, `multipleResponse`, `fillIn`, `numeric`) and diverse slide types (`treeCanvas`,
    `comparisonTable`, `scenarioPicker`, `verificationMatrix`, `branchingScenario`, `dragDropSet`)
    **strictly when pedagogically necessary** — never force complexity for the sake of novelty.
    - Use `ordering` when the subject matter is an actual chronological sequence / workflow steps (e.g. Alur Pekerjaan Tambah Kurang, Tahapan Klaim).
    - Use `matching` when mapping roles to responsibilities / RACI matrices.
    - Use `treeCanvas` for multi-role SOP diagrams with swimlanes.
    - Use `comparisonTable` when contrasting conditions (e.g. Pekerjaan Tambah vs Kurang).
    - Use standard `mcq` / `trueFalse` for conceptual comprehension and rule verification. Simple, clear communication always trumps gratuitous complexity.
15. **Sidebar Icons & Palette Uniformity**:
    - The outline navigation strictly adheres to corporate blue & slate (`#2B73BD`, `#38BDF8`, `#F0F4F7`, `#111C2E`). No rogue colors (e.g. green badges) in the outline.
    - Active slides use solid brand blue badge with white icon and pulse dot indicator; completed slides use subtle brand blue tint with brand blue checkmark; locked slides use muted badge with lock indicator.
    - Standardize and normalize unit icons (`ICON_NORMALIZATION`). Avoid casual or informal icons (such as `waving_hand`).
16. **Text Rendering & Rich-Text Invariants**:
    - Typography must render crisp and antialiased across displays (`-webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; text-rendering: optimizeLegibility;`).
    - All descriptive, lead, note, and explanation text runs through `formatRichText()` to support markdown bold (`**`), italic (`*`), inline code (`` ` ``), and safe HTML formatting without breaking mathematical comparison signs (`< Rp50 Miliar`, `> 10%`).
17. **Default Theme Configuration (`course.defaultDark`)**:
    - By default, modules initialize in dark mode (`defaultDark: true`).
    - When `course.defaultDark: false` is declared in `content.json`, the builder strips static `dark` classes from `<body>`, initializes `state.isDarkMode: false`, and boots in Light Mode (`#F0F4F7`) while preserving full dynamic theme switching via `#btnThemeToggle`.
18. **Certificate Live Preview & Print Contract**:
    - The `summaryCertificate` slide renders an in-slide live certificate preview card with real-time recipient identity (`state.participantName`), NIP, deterministic registration number (`getCertRegNumber()`), issue date, and evaluation score.
    - `@media print` ensures `#certificatePrintArea` renders as `display: flex` with clean A4 landscape bounds.

## Output format

Final deliverable: one self-contained `.html` file at the `--output` path, roughly 250–280 KB. The
user can open it via `file://`, host it on any static server, package it as SCORM
(`scripts/package_scorm.py`), embed it via `<iframe>`, or print certificates to PDF.

## Examples

### Example 1: Minimal 3-slide module

```json
{
  "course": { "code": "WELCOME-001", "title": "Welcome Module", "totalUnits": 3, "passingScore": 70, "totalQuestions": 2 },
  "brand": { "preset": "corporate" },
  "units": [
    { "title": "0. Welcome",  "icon": "info", "duration": "00:20", "category": "Intro" },
    { "title": "1. Concepts", "icon": "school", "duration": "01:00", "category": "Content" },
    { "title": "2. Quiz",     "icon": "quiz", "duration": "01:00", "category": "Quiz" }
  ],
  "slides": [
    { "type": "cover", "heroTitle": "Welcome", "heroLead": "...", "ctaLabel": "Start" },
    { "type": "cardList", "title": "3 Concepts", "cards": [ "...3 cards..." ] },
    { "type": "quiz", "questions": [ "...2 MCQs..." ] }
  ]
}
```

Note `passingScore` sits in `course`, never inside the quiz slide.

### Example 2: Convert prose to structured slides

User: "Slide 1 cover judul X. Slide 2 4 alasan perubahan. Slide 3 tree diagram alur. Slide 4 quiz 5 soal. Slide 5 sertifikat."

- "cover judul X" → `{"type": "cover", "heroTitle": "X", ...}`
- "4 alasan perubahan" → `{"type": "cardList", "cards": [...4 cards...]}`
- "tree diagram alur" → `{"type": "treeCanvas", "swimlaneData": [...], "flowCard": {...}}`
- "quiz 5 soal" → `{"type": "quiz", "questions": [...5 questions...]}`
- "sertifikat" → `{"type": "summaryCertificate", "takeaways": [...], "certificate": {...}}`

### Example 3: Mixed quiz types

```json
{
  "type": "quiz",
  "questions": [
    { "id": 1, "type": "mcq", "question": "...", "options": ["A","B","C","D"], "correctIndex": 0, "explanation": "..." },
    { "id": 2, "type": "trueFalse", "question": "...", "correctBool": true, "explanation": "..." },
    { "id": 3, "type": "fillIn", "question": "...", "acceptedAnswers": ["PFC","pfc"], "placeholder": "3 huruf...", "explanation": "..." }
  ]
}
```

## Frequently asked questions

**Can the user add a new slide type?**
Not via `content.json` alone. Add a renderer to `assets/shell.template.html`, register it in
`SLIDE_RENDERERS`, extend `assets/content.schema.json`, and update `references/slide_types.md`. Then
run the gates — the verifier fails if a `SLIDE_RENDERERS` entry has no matching function, or if the
registry and the schema disagree.

**Can the module use real audio narration?**
Yes. Drop MP3s at `./audio/unit_0.mp3`, `./audio/unit_1.mp3`, … next to the built HTML; the audio
engine auto-detects them. Generate them with `scripts/generate_audio.py`.

**How does certificate printing work?**
The user clicks "Cetak Sertifikat" on the summary slide; the engine fills the certificate nodes and
calls `window.print()`, producing an A4 (or your configured) landscape PDF via the `@media print`
rules. The button only appears once the quiz is passed. See "Custom certificate PDF".

**Can the module be embedded in an LMS?**
Yes — single self-contained HTML file. Embed via `<iframe>`, or ship it as SCORM with
`scripts/package_scorm.py`. Progress is **not** persisted across browser refreshes: state is
in-memory only by design.

**How do I update content after the first build?**
Edit `content.json`, re-run `build_module.py`, then re-run the verification gate with `--content` so
the stale-build check runs. The shell does not change between content updates.

## Failure modes to watch for

- **`Unknown slide type: <X>`** — a `type` outside the 21 supported. The validator now suggests the
  closest match.
- **`#slideBody` shows a red error** — a renderer threw. Check the browser console; usually a required
  field is missing (e.g. `cover` without `heroTitle`).
- **`goToSlide is not defined`** — a script block failed to parse; run `tools/verify_module.py`.
- **Certificate not rendering** — the quiz has not been passed yet. Check `state.quizCompleted` and
  `state.quizScore >= COURSE.course.passingScore`.
- **Certificate shows `__CERT_SIGNATORY__` (or similar)** — the build placeholder pass did not run, or
  a custom template used `__TOKEN__` instead of `{{token}}`; `build_module.py` now fails hard on this.
- **Colors look wrong (still PT PP blue)** — `brand.preset` did not resolve; it must match a key in
  `brand.profiles.json` (case-sensitive).
- **Tailwind classes not applying** — the Tailwind CDN failed to load; check connectivity.
- **Verification gate fails on "missing required ids"** — the static chrome was edited and an id the
  engine references was renamed or removed.
- **Verification gate fails on "COURSE literal does not match"** — the HTML is stale; rebuild.

## What NOT to do

- Don't write slide content into `assets/shell.template.html`. Content lives in `content.json`.
- Don't recreate or look for `scripts/build_shell_template.py` — the shell is canonical.
- Don't use a multi-file structure (separate JS/CSS); the shell is intentionally single-file.
- Don't add `localStorage` / `sessionStorage` persistence without an explicit user decision.
- Don't render slides server-side — everything runs client-side.
- Don't skip validation, the verification gate, or `self_check.py` after shell edits.
- Don't hardcode a machine path in commands or scripts — every script resolves the skill root
  relative to itself, an env var, or the user's home directory.
- Don't introduce brown/beige/tan accents or non-brand fonts; UI parity is required.

## Install locations and syncing

The skill is typically installed in more than one place (e.g. `~/.dsh/skills/modul-pp`,
`~/.gemini/config/skills/modul-pp`, and a workspace checkout). Pick **one canonical copy**, edit
there, and mirror it with `tools/sync_installs.py` (SHA256-verified) so the copies cannot drift.

## Reference paths (relative to skill root)

- `assets/shell.template.html` — the canonical engine (edit directly; re-run the gates after)
- `assets/content.schema.json` — JSON Schema for content.json
- `assets/brand.profiles.json` — 4 brand presets (ptpp / corporate / education / tech-startup)
- `assets/certificate.template.example.html` — starting point for a custom certificate
- `assets/sample.content.json` — working 21-slide example covering all 21 slide types
- `assets/sample.slide_breakdown.md` — example structured-bullets input
- `assets/project-runner/build_module.py` — portable per-project validate → build → verify runner
- `scripts/build_module.py` — content.json → final HTML
- `scripts/validate_content.py` — schema + slide diagnostics + semantic advisories
- `scripts/generate_audio.py` — Edge-TTS narration generator
- `scripts/package_scorm.py` — SCORM 1.2 / 2004 packaging
- `scripts/smoke_test_module.py` — headless-Chromium smoke test
- `scripts/self_check.py` — the skill's own regression gate (14 checks)
- `tools/verify_module.py` — offline verification gate (needs Node.js)
- `tools/sync_installs.py` — mirror a canonical copy to the other install locations
- `references/engine_behaviour.md` — runtime semantics: gates, quiz, webhook, SCORM, certificate
- `references/interactivity_patterns.md` — the Interactivity Map, 8 interaction patterns, placement
  rules, anti-patterns (read before choosing slide types)
- `references/interactivity_roadmap.md` — which interactive types are in scope, which are out, and the
  acceptance criteria for adding one
- `references/slide_types.md` — per-type field reference for all 21 slide types
- `references/input_format.md` — how the user should structure the slide breakdown input
- `references/brand_profiles.md` — brand preset details + how to add custom
- `references/pedagogical_patterns.md` — instructional patterns for interactive slides
- `references/gas_webhook_setup.md` — full Google Apps Script + Sheets setup
- `upstream/index_tree_canvas.html` — pinned design reference (read-only)
