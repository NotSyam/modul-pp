# Interactive Pedagogical Patterns Reference

To maximize learner engagement and prevent reading fatigue, every training module should incorporate diverse, purposeful interactive patterns across its units. Below are the 6 standard patterns proven in production modules.

---

## 1. 3D Flip Card (Flashcards / Values / Obstacles)
Ideal for: Core values, competencies, definitions, obstacles, and contrastive concepts.

### Key UX Specifications:
- **Card Container**: `perspective-1000 min-h-[250px] h-64 cursor-pointer`
- **Inner Container**: `relative w-full h-full duration-700 transform-style-3d transition-transform rounded-3xl shadow-sm border`
- **Front Face**: `flip-front absolute inset-0 backface-hidden p-4 sm:p-5 rounded-3xl flex flex-col justify-between overflow-y-auto`
- **Back Face**: `flip-back absolute inset-0 backface-hidden rotate-y-180 p-4 sm:p-5 rounded-3xl flex flex-col justify-between text-left overflow-y-auto`
- **Audio Feedback**: Call `playTone('click')` on card click.
- **Completion Trigger**: Track flipped cards in `state.flips = []`. When target count reached (e.g. 4 of 7), invoke `setTaskCompleted(unitId)`.

```html
<div class="flip-card min-h-[250px] h-64 perspective-1000 cursor-pointer" data-id="val1" data-flipped="false">
  <div class="flip-inner relative w-full h-full duration-700 transform-style-3d transition-transform rounded-3xl shadow-sm border border-slate-200">
    <div class="flip-front absolute inset-0 backface-hidden bg-white p-5 rounded-3xl flex flex-col justify-between overflow-y-auto">
      <div>
        <span class="text-[10px] font-bold uppercase text-slate-400">Pilar 01</span>
        <h4 class="text-sm font-extrabold text-slate-900 mt-1">Judul Konsep</h4>
        <p class="text-xs text-slate-600 mt-2 leading-relaxed">Deskripsi singkat bagian depan.</p>
      </div>
      <div class="pt-2 border-t text-[11px] font-bold text-emerald-600 flex justify-between">
        <span>Klik membalik</span>
        <svg class="w-3.5 h-3.5">...</svg>
      </div>
    </div>
    <div class="flip-back absolute inset-0 backface-hidden rotate-y-180 bg-slate-900 text-white p-5 rounded-3xl flex flex-col justify-between overflow-y-auto">
      <div>
        <span class="text-[10px] font-bold uppercase text-emerald-400">Penjelasan Lengkap:</span>
        <p class="text-xs text-slate-200 mt-2 leading-relaxed">Panduan perilaku detail atau studi analisis.</p>
      </div>
      <div class="text-right text-[10px] text-emerald-400 font-bold">✓ Terpelajari</div>
    </div>
  </div>
</div>
```

---

## 2. Interactive Comparison Matrix with Tabs
Ideal for: Comparing policies, job classifications (e.g. PNS vs PPPK), Do's and Don'ts, or old vs new regulations.

### Key UX Specifications:
- Filter buttons with `data-tab="all"`, `data-tab="groupA"`, `data-tab="groupB"`.
- Table rows or card rows with `data-group="groupA"`.
- Instant row filtering without page reload.
- Audio: `playTone('click')`.
- Task completion: User clicks at least 1 filter tab to inspect categories.

---

## 3. Keyword / Concept Explainer with Interactive Counters
Ideal for: Unpacking acronyms, multi-part definitions (e.g. FTTWH: Fungsi, Tugas, Tanggung Jawab, Wewenang, Hak), or core competencies.

### Key UX Specifications:
- Grid of interactive chip buttons with `data-kw="itemKey"`.
- Live preview display updating Title, Description, and Badge upon selection.
- Track unique clicked keys in `state.clickedKeys = []`.
- Badge showing live progress: `Ketuk 5 Kata Kunci (3/5)`.
- Task completes once all keys have been explored.

---

## 4. Quantitative Range Slider Simulator
Ideal for: Demonstrating the impact of progress, digital adoption percentage, budgeting, retirement age calculator, or score thresholds.

### Key UX Specifications:
- HTML `<input type="range" min="10" max="100" value="50" step="5" class="w-full accent-emerald-600">`.
- Live dynamic calculation updates in 3 metric cards below the slider:
  - Metric 1: Processing time (decreases as score increases).
  - Metric 2: Efficiency rating (percentage or badge).
  - Metric 3: User satisfaction / error rate.
- Audio: throttled or on-change tick.

---

## 5. Branching Ethical Dilemma & Field Scenario Matcher
Ideal for: Testing real-world decision making, ethics compliance, conflicts of interest, or standard operating procedure selection.

### Key UX Specifications:
- Present an authentic workplace dilemma scenario box.
- 3 to 4 actionable choices (buttons).
- Immediate color-coded feedback:
  - Correct choice: emerald background + `playTone('success')`.
  - Suboptimal / violation choice: rose background + `playTone('error')`.
- Feedback explainer showing the regulation rationale.

---

## 6. Evaluative Quiz Engine (Post-Test)
Ideal for: Final certification, assessment of learning outcomes, or gate to completion.

### Key UX Specifications:
- 8 to 15 multiple-choice questions.
- Question progress dots with live state indicators.
- Passing grade threshold: 75% or 80%.
- Score display with circular badge.
- Pass state: `playTone('fanfare')` + Canvas Confetti + "Lanjut ke Penutup" button.
- Fail state: `playTone('error')` + "Ulangi Kuis" button.

---

## 7. Interactive Video with Mid-Stream Cuepoint Quizzes & Clickable Hotspots
Ideal for: Video case studies, animated explainer comprehension checks, field simulation videos, SOP safety audits, and zero-distraction interactive walkthroughs.

### Native HTML5/JS Architecture (No Third-Party Authoring Tools Required):
Unlike expensive authoring tool subscriptions, this pattern runs directly in pure client-side HTML5 + Vanilla JS without external plugins:

1. **Video Container & Layer Stacking**:
   - The `<video>` element is wrapped in a `relative aspect-video rounded-2xl overflow-hidden group` container.
   - An interactive overlay layer (`absolute inset-0 z-30 pointer-events-none`) sits directly on top of the video canvas.

2. **Mid-Stream Pop-up Quizzes (Cuepoint Pause & Gate)**:
   - Configure timestamp cue points:
     `const cuePoints = [{ time: 14.5, type: 'quiz', id: 'cq1', triggered: false, question: '...', options: [...] }];`
   - Listen to `video.addEventListener('timeupdate', () => { ... })`:
     - When `video.currentTime >= cue.time && !cue.triggered`:
       - `video.pause()` automatically halts playback.
       - The overlay layer activates (`pointer-events-auto opacity-100 backdrop-blur-sm bg-slate-900/80`).
       - Displays an animated question card (Storyline-style popup).
       - Lock the seekbar to prevent cheating/scrubbing forward.
       - Correct answer invokes `playTone('success')` and unlocks a "Lanjutkan Video ▶" button.
       - Clicking continue hides the modal, marks `cue.triggered = true`, and calls `video.play()`.

3. **Clickable Video Hotspots (Visual Identification & Hazard Spotting)**:
   - At designated timestamps (e.g. between 00:22 and 00:32):
     - Display pulsing hotspot pins / glowing target boxes overlaying the video using percentage coordinates (`style="left: 64%; top: 38%;"`).
     - Video either pauses or slows down with prompt instructions: *"Klik APD helm kerja yang tidak sesuai standar pada teknisi!"*
     - Learner clicks the hotspot target:
       - Displays a detailed callout badge / information card.
       - Triggers `playTone('success')` and records task completion (`setTaskCompleted(unitId)`).
       - Resumes normal video playback.

