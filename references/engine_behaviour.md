# Engine behaviour reference

Everything on this page is implemented in `assets/shell.template.html` and configured from the
`course` block of `content.json`. Read it when you need exact runtime semantics, when a user asks
"does the module do X?", or before editing the shell.

`SKILL.md` holds the workflow; this file holds the internals.

---

## 1. Slide gate timer

- Enabled by default. `course.enableGatingTimer: false` disables it; `course.gatingSeconds`
  (default `10`) sets the duration. The engine reads `COURSE.course.enableGatingTimer !== false`,
  so any value other than an explicit `false` keeps the gate on.
- On a fresh slide `#btnNextSlide` is locked with a live countdown (`Tunggu (10s)` → `Tunggu (1s)`)
  and dimmed (`opacity-40 cursor-not-allowed`).
- The `#slideGateNotice` badge in the stage bar shows an amber countdown
  (`⏳ Selesaikan materi dalam Xs...`) and flips to emerald `Selesai Dipelajari` when the gate
  clears; a Web Audio unlock chime plays and the button gains the `btn-next-ready` pulse.
- Jumping ahead through the outline before the gate clears raises an educational notice:
  `Mohon pelajari materi ini terlebih dahulu. Anda dapat lanjut dalam X detik.`
- **Bypassed** for quiz/certificate slides and for slides already in `state.completedSlides`
  (revisiting a completed slide never re-locks it).

## 2. Quiz: attempts, identity, grading

- `course.maxQuizAttempts` (default `5`). The attempt counter is `state.quizAttemptCount`; the
  retake button shows the remainder (`Ulangi Kuis (Sisa X Percobaan)`).
- Pass (`score >= course.passingScore`, default `80`): certificate unlocks, confetti + fanfare,
  result synced to the webhook.
- Fail with attempts left: remedial evaluation card and a retake offer. That attempt is **not**
  synced.
- Fail on the final allowed attempt: the quiz locks permanently (retake button `disabled`) with
  `Kesempatan kuis Anda telah habis (5/5). Silakan hubungi Tim HC / PIC Pelatihan untuk evaluasi
  lebih lanjut.` This final failed attempt **is** synced, with status
  `TIDAK LULUS (MAX ATTEMPT)` — see the webhook section below.
- Question types can be mixed freely on one quiz slide: `mcq` (shuffled options), `trueFalse`,
  `fillIn` (case-insensitive against `acceptedAnswers`), `multipleResponse` (exact set), `ordering`
  (items shuffled for display, sequence graded), `matching` (right column shuffled, one choice per
  left row) and `numeric` (comma decimals accepted, optional absolute `tolerance`). One question per
  screen, post-submit review, answer key explanation.
- Grading is **binary per question** (right or wrong) and aggregates to a percentage; there is no
  partial credit. That keeps the pass threshold, the attempt limit, the certificate and the webhook
  payload unchanged no matter how many question types a quiz mixes.
- Every question type is implemented once in the shared question engine
  (`renderQuestionInput` / `isAnswerCorrect` / `displayAnswer` / `displayCorrectAnswer` / `isAnswered`)
  and used by both the graded quiz and the formative checkpoint. Adding a type means touching those
  five functions plus the schema — not each renderer.
- **Participant identity card** is collected on the **quiz slide**, not the certificate slide:
  Nama Lengkap, NIP/NRP, Jabatan, Divisi/Unit Kerja. Set `"askParticipantInfo": false` on the quiz
  slide to hide the card *and* skip the required Nama/NIP validation — use it for anonymous or
  refresher modules.
- **Attempt limit is a soft limit.** All state lives in memory only (deliberately no
  `localStorage`/`sessionStorage`), so a page reload resets `quizAttemptCount` to zero. Treat the
  limit as a nudge, not as an anti-cheat control. If a deployment genuinely needs enforcement,
  that requires a server-side check keyed on NIP — not a shell tweak.

## 2b. Formative checkpoint block

Any slide may carry an optional `checkpoint` object; `renderCurrentSlide()` mounts it into
`#checkpointPanel` below the slide body after the type renderer runs (so it works on all 21 types).

- Rendered panel: prompt + one question (any of the 7 types) + a **Periksa** button + inline feedback
  (`role="status"`, `aria-live="polite"`) and, on success, the question's `explanation`.
- **Formative boundary:** `checkCheckpoint()` writes only to `state.checkpointResult` and
  `state.checkpointAnswers`. It never touches `quizScore`, `quizAttemptCount`, `quizCompleted` or the
  webhook payload. `scripts/smoke_test_module.py` asserts exactly that (`scoreUntouched`).
- Empty answers are rejected before grading (`isAnswered`) with an in-app notice, not a score of 0.
- On a correct answer it calls `completeCurrentSlideTask()`: the slide is marked complete and the
  10-second gate releases early. It never blocks navigation — a wrong answer just invites a retry.
- State is in memory only, like everything else: a reload resets checkpoints.

## 2c. Hotspot image (`hotspotImage`)

An image with percentage-positioned hotspot pins, in two modes:

- **`explore`** (default): every pin is informative. Clicking or keyboard-activating a pin sets it
  active and shows `title`/`body` in `#hotspotDetail`. Pins carry their `label` (numbered tour).
- **`find`**: only pins with `"correct": true` count. A decoy click is recorded in
  `state.hotspots[slide].wrong`, painted red and explained with `wrongNote`; it never completes the
  exercise.

Runtime contract:

- Progress is `state.hotspots[<slideIndex>] = { found: [], active, wrong: [] }`, updated by
  `openImageHotspot()` and rendered by `refreshHotspotImage()` (targeted DOM refresh — it does not
  re-render the slide, so scroll position survives).
- Positions are **percentages** (`x`/`y` 0–100), so pins track the image at any viewport size.
- Pins are real `<button>`s inside the image container: Tab reaches them, Enter/Space activates them,
  `aria-pressed` reflects the active pin, and the detail panel is `role="status" aria-live="polite"`.
- **Formative only.** Opening every pin (or every correct pin in `find`) shows `completeNote` and
  calls `completeCurrentSlideTask()` — the score, attempt counter and webhook are untouched
  (`scripts/smoke_test_module.py` asserts `formative: score=0 attempts=0`).
- `src` may be a relative path or a `data:` URI (the sample uses an inline SVG), so the module can
  stay a single file. Keep the asset small: a flat SVG is a few KB, a 300 DPI PNG is hundreds.

## 2d. Branching scenario (`branchingScenario`)

- State: `state.branching[<slideIndex>] = { node, picks: [{label, correct}], done, correct, feedback }`,
  initialised from the slide's `start` node.
- `branchChoose()` records the pick, carries the chosen `feedback` into the next node (rendered as the
  "Konsekuensi" banner), and detects endings: either `choice.next` resolves to a node with
  `ending: true`, or the choice has no `next` (a terminal choice is its own ending).
- Correct ending → success tone + `completeCurrentSlideTask()` (gate release). Wrong ending → error
  tone, debrief shown, restart offered. `restartBranching()` resets only that slide's walk.
- `refreshBranchingScenario()` swaps `#branchingStage` and the breadcrumb, then moves focus to the new
  node heading (`[data-bs-focus] tabindex="-1"`), so keyboard and screen-reader users follow the
  conversation instead of being stranded on the old button.
- Formative: no writes to `quizScore`, `quizAttemptCount` or the webhook payload.

## 2e. Drag-drop set (`dragDropSet`)

- State: `state.dragdrop[<slideIndex>] = { placed: {itemId: bucketId}, selected, checked, results, dragging }`.
- **Click-to-place is the primary path** and the only one required for compliance: select an item
  (`toggleDragItem`), then press the bucket's place button (`placeDragItem`). Clicking an already
  placed item returns it to the pool. HTML5 `dragstart`/`drop` (`startDragItem` / `dropDragItem`)
  feeds the same state for mouse users — touch devices use the click path automatically.
- `checkDragSet()` requires every item to be placed, then records `results[itemId] = placed === expected`
  and paints right/wrong. Any subsequent move clears `checked`/`results` so the learner can retry.
- All correct → success note + `completeCurrentSlideTask()` (gate release). Formative only.
- `paintDragDrop()` re-renders the pool, the buckets and the feedback line after every change; it is
  also called from the post-render hook because the pool/buckets need the live DOM.
- Chips are 44px buttons with `aria-pressed`; buckets expose a labelled place button, so the exercise
  is operable with Tab + Enter alone.

## 3. Google Sheets webhook sync

- Fired from the quiz flow with `fetch(webhookUrl, {method:'POST', headers:{'Content-Type':
  'text/plain;charset=utf-8'}, body: JSON.stringify(payload)})`. The `text/plain` content type is
  deliberate: it keeps the request a "simple request" so the browser does not send a CORS
  preflight that Apps Script cannot answer.
- Payload: `nama`, `nip`, `jabatan`, `divisi`, `skor`, `status`, `attempt`.
- Endpoint resolution: slide-level `webhookUrl` wins, otherwise `course.webhookUrl`.
- **Sync condition:** `state.quizPassed || (state.quizAttemptCount >= maxAttempts)`. Passing
  results always sync; a failure syncs only when it exhausts the attempt limit, so remedial
  attempts do not pollute the sheet but a permanent failure is still recorded.
- Network errors are swallowed with a console warning (`.catch(err => console.warn(...))`) — a
  dead webhook never blocks the learner.
- There is **no authentication** on the request: anyone who reads the published HTML can post to
  the endpoint. If that matters, add a shared secret or a `moduleId` field and filter server-side.
- Receiver script, idempotent and concurrency-safe (upsert-highest): see section 7 below.

## 4. SCORM runtime

`findSCORMAPI` / `initSCORM` / `recordSCORMProgress` / `finishSCORM` talk to the LMS SCORM API when
the module runs inside a SCORM player, and silently no-op in a plain browser. Package a built module
for an LMS with:

```bash
python3 <skill-root>/scripts/package_scorm.py \
  --html <project-dir>/index.html \
  --content <project-dir>/content.json \
  --version 1.2 \
  --output <project-dir>/module_scorm.zip
```

`--content` is optional: without it the packager parses the injected `COURSE` literal out of the
HTML (brace-matched, not regex-sniffed). Pass `--audio-dir ./audio` to bundle narration;
`--assets-dir` bundles a logo folder.

Note the design tension: the engine is in-memory only, while SCORM implies progress tracking. The
SCORM calls report progress to the LMS, but a browser refresh still restarts the module unless the
LMS itself reopens it with suspended data.

## 5. Dev/review mode & Quiz Bypass

There are four ways to review and test modules without being blocked by gate timers or having to complete every quiz question:

- **`course.devMode: true`**:
  - Unlocks slide hopping and disables gating countdown timers.
  - Automatically displays the `⚡ Bypass Kuis (Dev Testing)` button directly on the quiz slide.
  - Shows the `#previewModeBadge` for runtime toggle.
- **`course.bypassQuiz: true`**:
  - Declared directly in `content.json` under `course`.
  - Automatically marks the quiz as completed (`quizPassed: true`, score `100%`) and unlocks the certificate slide immediately.
  - Pre-fills sample participant identity credentials (`Nama Peserta Contoh` / `12345678`) so the certificate can be printed instantly.
  - Unlocks all units in the outline navigation sidebar.
- **In-Slide Testing Button (`⚡ Bypass Kuis (Dev Testing)`)**:
  - When `bypassQuiz: true` or `devMode: true`, an amber dev button appears on the quiz slide (`devBypassQuiz()`). Clicking it instantly completes the quiz with a 100% score and jumps straight to the certificate slide.
- **URL Hash Shortcut `#cert-preview`**:
  - Opening `index.html#cert-preview` in any browser immediately renders the certificate modal at true A4 print scale with sample data for rapid `Ctrl+P` PDF layout tuning.

## 5b. Sidebar outline & iconography

- **Palette**: strictly PT PP corporate blue & slate (`#2B73BD`, `#38BDF8`, `#F0F4F7`, `#111C2E`). No rogue colors (e.g. green badges) exist in the outline navigation.
- **States**:
  - *Active Slide*: solid brand blue badge with white icon, left blue border accent, pulse dot indicator.
  - *Completed Slide*: subtle brand blue badge (`bg-brand-primary/10 text-brand-primary`), clean brand blue checkmark.
  - *Unlocked Slide*: clean slate badge (`bg-slate-100 text-slate-500`).
  - *Locked Slide*: muted badge with small lock icon on the right, cursor-not-allowed.
- **Icon Normalization**: casual or informal icons (such as `waving_hand`) are automatically mapped to professional corporate symbols (`explore`, `menu_book`, etc.) via `ICON_NORMALIZATION`.

## 5c. Text rendering & rich-text formatting

- **Font Smoothing**: all typography is rendered with `-webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; text-rendering: optimizeLegibility;` on `html, body`.
- **`formatRichText(input)`**:
  - Markdown bold (`**text**`), italic (`*text*`), and inline code (`` `code` ``).
  - Robust HTML tag whitelist supporting attributes (`class`, `style`) while sanitizing dangerous handlers (`on*`, `javascript:`).
  - Entity-safe character replacement that preserves mathematical symbols (`< Rp50 Miliar`, `> 10%`) and does not double-escape existing HTML entities (`&nbsp;`, `&amp;`).
  - Safe token restoration via `split().join()` preventing regex special replacement character injection.

## 6. Certificate printing

- Unlock condition: `!hasQuiz || (state.quizPassed && state.quizScore >= passingScore)`.
- `printCertificate()` fills `#certScoreVal`, `#certRecipientName`, `#certRecipientNIP`,
  `#certNumberLabel` and `#certDateVal`, reveals `#certificatePrintArea`, calls `window.print()`,
  then hides the area again after 1s. Every write is null-guarded, so a custom template that omits
  an optional node cannot throw.
- Registration number is **deterministic**: a hash of `NIP | course code | year`, zero-padded to
  `course.certificate.regSequenceDigits` (default 4) and formatted by
  `course.certificate.regNumberFormat` (default `{prefix}/{year}/{seq}`). Reprinting the same
  learner's certificate therefore yields the same number — mutable random numbers made
  certificates unauditable.
- Print CSS: everything is hidden except `#certificatePrintArea`, sized by
  `course.certificate.pageSize` / `pageWidthMm` / `pageHeightMm` with `printPadding` (default
  `15mm`; use `0` for a full-bleed design). Output is PDF via the browser print dialog.
- **Custom template:** `course.certificate.template` points at an HTML fragment that replaces the
  inner markup of `#certificatePrintArea` (the region between the `CERT-TEMPLATE-START` and
  `CERT-TEMPLATE-END` comments in the shell). It may use `{{token}}` build-time values and must
  keep the five contract ids `certRecipientName`, `certRecipientNIP`, `certScoreVal`,
  `certDateVal`, `certNumberLabel`. An unknown `{{token}}` fails the build; `tools/verify_module.py`
  fails the gate when a contract id is missing. Start from
  `assets/certificate.template.example.html`.
- **Labels** (kicker, presented-to line, pass note, score label, threshold note, date label, footer
  note) are overridable through `course.certificate.labels`, because the built-in wording is
  Indonesian corporate boilerplate. The pass threshold text follows `course.passingScore` — it is
  no longer hardcoded to 80%.
- **Preview mode:** opening the module with `#cert-preview` in the URL calls `showCertificatePreview()`
  on boot. It injects sample participant data (`Nama Peserta Contoh` / `12345678` / score `92`),
  reveals `#certificatePrintArea` at true page size over the player, and adds a `.no-print` badge.
  `fillCertificate()` is shared by the preview and the real print, so the preview cannot drift from
  the printed output. Disable it by removing the hash; nothing is persisted.
- Shipped templates: `assets/certificate.template.example.html` (portrait award card) and
  `assets/certificate.template.modern.html` (landscape, full-bleed navy sidebar).

## 7. Google Apps Script receiver (idempotent, upsert-highest)

```javascript
function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.tryLock(10000); // Mencegah race condition (aman untuk 50+ peserta serentak)

  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);

    var newNip = String(data.nip || "").trim();
    var newScore = Number(data.skor) || 0;

    if (!newNip) {
      return ContentService.createTextOutput(JSON.stringify({result: "error", message: "NIP wajib ada"}))
        .setMimeType(ContentService.MimeType.JSON);
    }

    var lastRow = sheet.getLastRow();
    var foundRowIndex = -1;
    var existingScore = -1;

    // Header diasumsikan ada di baris 1:
    // Col 1: Timestamp | Col 2: Nama | Col 3: NIP | Col 4: Jabatan | Col 5: Divisi | Col 6: Skor | Col 7: Status | Col 8: Attempt
    if (lastRow > 1) {
      var nipRange = sheet.getRange(2, 3, lastRow - 1, 1).getValues(); // Kolom NIP (Kolom C)
      var scoreRange = sheet.getRange(2, 6, lastRow - 1, 1).getValues(); // Kolom Skor (Kolom F)

      for (var i = 0; i < nipRange.length; i++) {
        if (String(nipRange[i][0]).trim() === newNip) {
          foundRowIndex = i + 2;
          existingScore = Number(scoreRange[i][0]) || 0;
          break;
        }
      }
    }

    if (foundRowIndex > -1) {
      // Jika NIP sudah ada, HANYA TIMPA jika nilai baru LEBIH TINGGI
      if (newScore > existingScore) {
        sheet.getRange(foundRowIndex, 1).setValue(new Date());
        sheet.getRange(foundRowIndex, 2).setValue(data.nama);
        sheet.getRange(foundRowIndex, 4).setValue(data.jabatan);
        sheet.getRange(foundRowIndex, 5).setValue(data.divisi);
        sheet.getRange(foundRowIndex, 6).setValue(newScore);
        sheet.getRange(foundRowIndex, 7).setValue(data.status);
        if (data.attempt) sheet.getRange(foundRowIndex, 8).setValue(data.attempt);

        return ContentService.createTextOutput(JSON.stringify({result: "updated", message: "Data lama ditimpa dengan nilai lebih tinggi"}))
          .setMimeType(ContentService.MimeType.JSON);
      } else {
        return ContentService.createTextOutput(JSON.stringify({result: "skipped", message: "Nilai lama lebih tinggi atau sama, tidak ditimpa"}))
          .setMimeType(ContentService.MimeType.JSON);
      }
    } else {
      // Jika NIP belum ada sama sekali, tambahkan baris baru
      sheet.appendRow([
        new Date(),
        data.nama,
        data.nip,
        data.jabatan,
        data.divisi,
        newScore,
        data.status,
        data.attempt || 1
      ]);
      return ContentService.createTextOutput(JSON.stringify({result: "created", message: "Baris baru berhasil ditambahkan"}))
        .setMimeType(ContentService.MimeType.JSON);
    }
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({result: "error", error: err.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}
```

Full setup walkthrough: `references/gas_webhook_setup.md`.

## 8. Learner-experience invariants (do not regress)

Each of these was requested by real users during module reviews. They are **already implemented**.
Do not re-derive them, and do not silently revert them when editing the shell — if a reviewer asks
for a change that contradicts one, treat it as a deliberate override and say so in your report.

| Behaviour | Where | Why learners asked for it |
|---|---|---|
| **Narration autoplays on slide entry** | `goToSlide()` → `if (slideIndex > 0 \|\| state.hasUserNavigated) startPlayAudio()` | Manual play-click on every slide was the #1 friction point. The cover slide stays silent until "Mulai". |
| **Single scroll track** | `#stageBackdrop` is `overflow-hidden` + `items-center justify-center`; `#slideViewport` is `h-full max-h-[880px]`; only `#slideBody` scrolls | Double/triple nested scrollbars made the module feel broken on laptops. |
| **In-app notices, never `alert()` / `confirm()`** | `showGatingNotice()` renders into `#toastHost`; the "unanswered questions" confirmation is a two-step button press | Native dialogs clash with the design system and block scripted/automated runs. `tools/verify_module.py` reports them as an advisory. |
| **Sticky table header** | `comparisonTable` `<thead> <tr>` carries `sticky top-0 backdrop-blur-sm z-10` | Long comparison tables lost their column meaning on scroll. |
| **Deep corporate navy in light mode** | `body:not(.dark)` uses `#0F243E`; `uiTitle()` `<h2>` too | Slate-900 read as "generic SaaS"; navy reads as institutional. |
| **Cheat-sheet value pills** | `initCheatSheet()` — left-aligned card, value inside a `bg-brand-primary/10` pill, honouring `wide: true` | Centred cards with a bare number were unreadable as a reference sheet. |
| **Base64 logo** | `course.logo` accepts a full `data:image/png;base64,…` URI | Makes the module genuinely single-file; no `assets/` folder to lose. |
| **Deterministic certificate number** | `certSequenceNumber()` in the shell | A random per-print number made issued certificates impossible to verify. |

## 9. Audio narration contract

- The engine requests `./audio/unit_<slideIndex>.mp3` (0-based, resolved next to the built HTML).
- If the file is absent it runs a 45-second simulator that drives the seekbar identically and calls
  `completeCurrentSlideTask()` at the end, so the gate still clears.
- Caption dock + Transkrip tab text comes from `slides[N].narration` first, then
  `COURSE.narration[N]`, and are independent of whether an MP3 exists.
- `scripts/generate_audio.py` produces those MP3s and, when a slide has no narration at all,
  synthesises an "intisari" script from the slide's own copy rather than skipping it.

## 10. Header logo and balanced card grids

**Logo.** The header logo block in `shell.template.html` is wrapped in `<!-- LOGO-START -->` /
`<!-- LOGO-END -->`. `build_module.py` resolves the image and ships one of three variants (the markers
themselves are stripped from the output):

| Condition | Rendered | Dark mode |
|---|---|---|
| `logo` + `logo-dark` | two `<img>`s (`dark:hidden` / `hidden dark:block`) | dedicated asset, no filter |
| `logo` only | one `<img>` with `dark:brightness-0 dark:invert` | white silhouette |
| no logo file | monogram badge from the brand name | inherited brand colours |

Resolution order: a `data:` URI in `course.logo` is kept as-is; a declared path that exists is inlined;
otherwise conventional filenames (`logo`, `brand`, `brand-logo` × png/jpg/jpeg/svg/webp/gif) are looked
up in the content folder and its `assets/`, `img/`, `images/` subfolders. All logos are base64-inlined,
so the module stays a single file. `--logo` / `--logo-dark` override detection.

**Card grids.** `.cardgrid` is a centred flex row: the column count still comes from `data-cols`, but a
partial last row is centred instead of hugging the left edge with dead space beside it. Used by
`cardList` (columns ≥ 2), `imageGallery`, `kpiDashboard` (3 columns), `docTabs` cards and the
certificate takeaways. `data-gap` adjusts the gap (`2`, `4`) to match the original spacing.
