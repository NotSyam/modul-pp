# Slide Types Reference

This document describes all **21 slide types** supported by the Modul PP skill. For each type, it lists:
- **Visual layout** the type produces
- **Required fields** (will render blank/broken if missing)
- **Optional fields** (silently ignored if absent)
- **Example payload** (minimal valid)

Use this as the canonical reference when picking slide types from the user's content breakdown.

---

## Type taxonomy

| # | Type | Visual | Best for |
|---|------|--------|-----------|
| 1 | `cover` | Hero gradient card + 4-card grid + CTA | Module opener, "welcome" slide, course intro |
| 2 | `cardList` | Stacked / grid of icon+title+desc cards | Concepts, definitions, key points, multi-card content |
| 3 | `treeCanvas` | Pan/zoom diagram with hotspot nodes | Process flows, swimlane diagrams, decision trees |
| 4 | `scenarioPicker` | Click-to-reveal verdict cards | "What-if" scenarios, branching logic, compliance checks |
| 5 | `tabbedAccordion` | Tabbed panels + optional `<details>` checklists | Multi-aspect content (agenda + output, etc.) |
| 6 | `verificationMatrix` | Tabbed lists mapping docs → PIC | Document checklists, RACI matrices |
| 7 | `twoCardAccordion` | 2 centered cards side-by-side + mini-check | Compare/contrast (hardcopy vs softcopy) |
| 8 | `docTabs` | Tabbed lists of documents/records/attachments | Document inventory, attachments catalog |
| 9 | `kpiDashboard` | KPI grid + interactive audit checklist | Performance measurement, KPI tracking |
| 10 | `riskCards` | Stacked cards (no/proc/risk/mitigation) | Risk register, risk analysis |
| 11 | `quiz` | 1-question-per-screen, post-submit review | Knowledge check, certification gate |
| 12 | `summaryCertificate` | Hero score + takeaways + cert inputs | Closing slide, certificate trigger |
| 13 | `imageGallery` (new) | Grid or carousel of images | Photo collections, diagrams, screenshots |
| 14 | `videoEmbed` (new) | YouTube / Vimeo / direct mp4 | Video-based learning, demos |
| 15 | `calloutBox` (new) | Info/warning/success/danger banner | Important notes, warnings, tips |
| 16 | `stepByStep` (new) | Numbered vertical timeline | Step-by-step procedures, workflows |
| 17 | `comparisonTable` (new) | Tabular comparison with column highlight | Feature comparison, before/after |
| 18 | `faqAccordion` (new) | Collapsible Q&A list | FAQ, common questions |
| 19 | `hotspotImage` | Image + keyboard-operable hotspot pins | Labeled graphics, guided image tours, find-the-target exercises |
| 20 | `branchingScenario` | Decision tree: situation → choices → endings | Judgement calls, escalation, customer handling, troubleshooting paths |
| 21 | `dragDropSet` | Item pool + buckets, click-to-place or drag | Categorising documents, risks, roles; sorting rules into groups |

---

## 1. `cover` — Module opener

```json
{
  "type": "cover",
  "category": "Pendahuluan",
  "heroTitle": "Course Title",
  "heroLead": "Short tagline (1-2 sentences)",
  "heroMeta": "CODE-001 · 2026 · version info",
  "ctaLabel": "Mulai Pembelajaran",
  "ctaIcon": "play_arrow",
  "skipTo": 1,
  "reasons": [
    { "icon": "verified", "title": "Reason 1", "desc": "Why this course matters" },
    { "icon": "monitoring", "title": "Reason 2", "desc": "..." }
  ]
}
```

**Required**: `heroTitle`
**Optional**: `heroLead`, `heroMeta`, `ctaLabel` (default "Mulai Pembelajaran"), `ctaIcon` (default `play_arrow`), `skipTo` (default 1), `reasons[]` (4-card grid)

---

## 2. `cardList` — Multi-card content

```json
{
  "type": "cardList",
  "category": "Konsep",
  "title": "Tiga Pilar Inti",
  "lead": "Tiga konsep yang wajib dipahami",
  "columns": 1,
  "cards": [
    { "icon": "looks_one", "title": "Pilar 1: Definisi", "desc": "...", "tags": ["definisi"] },
    { "icon": "looks_two", "title": "Pilar 2: Proses",  "desc": "...", "body": "<p>Extra HTML</p>" }
  ]
}
```

**Required**: `cards[]` (each: `title` + `desc` required; `icon`, `body`, `tags[]` optional)
**Optional**: `columns` (1, 2, or 3 — default 1)

---

## 3. `treeCanvas` — Authentic 3-column pan/zoom diagram

Renders the **authentic PT PP-style 3-column tree diagram** from the original reference file. Each phase becomes a `#fase-N` container; each item becomes a row with three columns:

| Col-span | Content |
|----------|---------|
| **col-span-3 (left)**  | **Dokumen Input** box — lists `item.inputs[]` |
| **col-span-6 (center)** | **Aktivitas** node — clickable button with actor badge, step number, title, and (for decisions) branches rendered inline |
| **col-span-3 (right)** | **Dokumen Output** box — lists `item.outputs[]` OR (for decisions) "Cabang Keputusan" indicator |

Between rows: down-arrow connector (`↓`). Click any center node → hotspot modal with full item detail (peran, input, output, klausul). Pan/zoom engine + role filter + phase-jump buttons + custom scrollbar all included.

```json
{
  "type": "treeCanvas",
  "category": "Alur Proses",
  "title": "Tree Diagram",
  "lead": "Klik node untuk detail",
  "swimlaneData": [
    {
      "section": "Fase 1: Persiapan",
      "sectionIcon": "rocket_launch",
      "items": [
        {
          "id": "step_1_1",
          "step": "1.1",
          "actor": "PM",
          "actorRole": "Project Manager",
          "actorColor": "bg-brand-primary text-white",
          "title": "Kick-off & Definisi Scope",
          "inputs": ["Project Charter", "Kontrak"],
          "outputs": ["Scope Statement"],
          "clauses": ["1.1 PM memimpin rapat kick-off.", "<strong>Aturan Mutasi:</strong> ..."],
          "isDecision": false
        }
      ]
    }
  ],
  "flowCard": {
    "step_1_1": { "t": "Kick-off & Definisi Scope", "out": "Scope Statement" },
    "step_decision_review": {
      "t": "Review Mutu (Keputusan)",
      "branches": [["Ya (Lolos)", "Lanjut ke BAST I"], ["Tidak", "Rework + re-inspeksi"]]
    }
  },
  "roleFilterOptions": ["Semua", "PM", "GM", "SVP"],
  "phaseJumps": [
    { "id": "fase-1", "label": "Fase 1: Persiapan" },
    { "id": "fase-2", "label": "Fase 2: Eksekusi" }
  ]
}
```

**Required**: `swimlaneData[]` (each item: `id` + `step` + `title` minimum; `actor`, `actorRole`, `inputs[]`, `outputs[]`, `clauses[]`, `isDecision` optional)
**Optional**: `flowCard` (map of stepId → `{t, out?, branches?}`), `roleFilterOptions` (default `["Semua"]`), `phaseJumps[]`

Notes:
- `clauses[]` items allow HTML (e.g., `<strong>...</strong>`)
- Decision nodes have `step: "KEPUTUSAN"` and `isDecision: true` (or have `flowCard[id].branches`)
- `flowCard` items with `branches` render their branches inline inside the center column (sky-blue decision card)
- `flowCard[id].t` overrides the title shown in the center node (useful for shortening display names)
- `flowCard[id].out` overrides the output box label (useful for compact output strings)
- The `id` field of each swimlane item is matched against `flowCard` keys to find the card display data
- Phase container IDs default to `fase-1`, `fase-2`, ... OR use `phaseJumps[].id` if provided (must match for `jumpToPhase()` to work)
- Pan/zoom + role filter + phase jump are all engine-driven — just provide the data
- The 1100px-wide inner content + 640-700px tall viewport matches the original reference file exactly

---

## 4. `scenarioPicker` — Click-to-reveal verdicts

```json
{
  "type": "scenarioPicker",
  "category": "Ketentuan",
  "title": "Scenario Compliance Check",
  "lead": "Klik tiap skenario untuk lihat verdict",
  "infoBanner": "<strong>Note:</strong> Semua skenario mengacu ke Poin 6.1-6.3.",
  "cards": [
    { "icon": "info", "title": "Aturan Mutu", "desc": "Pelaksanaan mutu wajib mengikuti SOP" }
  ],
  "scenarios": [
    {
      "id": "compliance",
      "label": "Skenario A",
      "title": "Pilih kondisi mutu",
      "options": [
        { "id": "ok",     "label": "Lolos",          "verdict": "Lanjut ke BAST I.",      "tone": "positive" },
        { "id": "fail",   "label": "Tidak Lolos",   "verdict": "Rework + re-inspeksi.",  "tone": "negative" }
      ]
    }
  ]
}
```

**Required**: `scenarios[]` (each: `id`, `label`, `options[]` — each option: `id`, `label`, `verdict`)
**Optional**: `infoBanner` (HTML allowed), `cards[]` (info cards above scenarios)
**Tone values**: `positive` (green), `negative` (red), `neutral` (gray)

---

## 5. `tabbedAccordion` — Multi-aspect content

```json
{
  "type": "tabbedAccordion",
  "category": "Ketentuan",
  "title": "Hold Point V Agenda & Output",
  "lead": "12 agenda + 7 output wajib",
  "tabs": [
    {
      "key": "agenda",
      "label": "Agenda",
      "items": ["Pembahasan CSS 100%", "Evaluasi sisa waktu", "..."]
    },
    {
      "key": "output",
      "label": "Output",
      "items": [
        { "t": "BA Hold Point V", "d": "Didistribusikan ke Divisi Operasi" },
        { "t": "Laporan Tutup Buku I", "d": "..." }
      ]
    }
  ],
  "checklist": [
    { "label": "Mini-check", "items": ["Item 1", "Item 2"] }
  ]
}
```

**Required**: `tabs[]` (each: `key`, `label`, `items[]`)
**Items**: either plain strings OR `{t, d}` objects (title + description)
**Optional**: `checklist[]` (mini `<details>` accordions below the tabs)

---

## 6. `verificationMatrix` — Doc → PIC mapping

```json
{
  "type": "verificationMatrix",
  "category": "Ketentuan",
  "title": "Verifikasi Dokumen",
  "lead": "Mapping dokumen → PIC",
  "tabs": [
    {
      "key": "tb1",
      "label": "Tutup Buku I",
      "defaultPic": "GM-Ops (DVO)",
      "items": [
        { "doc": "As Built Drawing" },
        { "doc": "Dokumen ADM & KEU", "note": "TTD PM, SM-FinHC & GM-Ops", "pic": "GM-Ops (DVO)" },
        { "doc": "BA HP V", "pic": "GM-Ops (DVO) & SVP-OC&SCC", "noInfo": true }
      ]
    }
  ]
}
```

**Required**: `tabs[]` (each: `key`, `label`, `items[]` — each item: `doc`)
**Optional**: `defaultPic` (used if item.pic absent), `note`, `pic`, `noInfo` (boolean — compact row without note space)
**Optional (slide level)**: `legend` — text of the sky-blue legend pill rendered on each panel (default `"PIC Khusus"`); `defaultPic` — verifier label used when neither the row nor the tab supplies one

---

## 7. `twoCardAccordion` — Side-by-side compare

```json
{
  "type": "twoCardAccordion",
  "category": "Ketentuan",
  "title": "Hardcopy vs Softcopy",
  "infoBanner": "Dokumen wajib diserahkan dalam 2 format.",
  "infoBannerIcon": "info",
  "cards": [
    { "icon": "description", "title": "Hardcopy", "desc": "Versi cetak", "items": [{"label":"Jilid", "value":"3 rangkap"}] },
    { "icon": "folder",     "title": "Softcopy", "desc": "Versi digital", "items": [{"label":"Format", "value":"PDF + Excel"}] }
  ],
  "miniCheck": [
    { "label": "Checklist penyerahan", "items": ["TTD PM", "Stempel proyek"] }
  ]
}
```

**Required**: `cards[]` (exactly 2 elements; each: `title`, `desc`)
**Optional**: `infoBanner`, `infoBannerIcon`, `cards[].items[]` (label/value pairs), `miniCheck[]`

---

## 8. `docTabs` — Document inventory

```json
{
  "type": "docTabs",
  "category": "Dokumen",
  "title": "Dokumen, Record & Lampiran",
  "tabs": [
    { "key": "doc",  "label": "Dokumen Terkait", "itemType": "list",        "items": ["Form BAST I", "Form BAST II"] },
    { "key": "rec",  "label": "Record Wajib",    "itemType": "records",    "items": ["Rencana Anggaran", "Final PFC"] },
    { "key": "lamp", "label": "Lampiran",         "itemType": "attachments", "items": ["Form Pembebanan", "Form Tutup Buku"] }
  ]
}
```

**Required**: `tabs[]` (each: `key`, `label`, `items[]`)
**itemType values**:
- `list` (default) — icon-prefixed list items
- `records` — numbered "01", "02", ... prefix
- `attachments` — "Lamp. 1", "Lamp. 2", ... prefix

**Items**: plain strings OR `{doc, note}` objects

**Optional tab-level `chip`**: prefix for that tab's record chips, e.g. `"chip": "8."` renders `8.01`, `8.02`. Defaults to a zero-padded index.
**Optional item extras**: `code` (mono document code), `icon`, and `hero: true` — when the first item of a tab carries `code` or `hero`, it is promoted to the prominent linked-document hero card (`w-12 h-12` icon box + mono code + bold title + description), matching the reference module.

---

## 9. `kpiDashboard` — KPI + audit checklist

```json
{
  "type": "kpiDashboard",
  "category": "Performance",
  "title": "Performance Measurement",
  "lead": "Tolok ukur keberhasilan",
  "kpis": [
    { "label": "Tujuan",   "value": "100%", "target": "≥ 95%", "desc": "Kelengkapan dokumen", "icon": "verified" },
    { "label": "Cara",    "value": "Audit", "desc": "Cara pengukuran", "icon": "fact_check" },
    { "label": "Target",  "value": "100%", "desc": "Tingkat kepatuhan", "icon": "target" }
  ],
  "auditChecklist": [
    { "id": "audit_1", "label": "As Built Drawing tersedia" },
    { "id": "audit_2", "label": "BAST I sudah ditandatangani" }
  ]
}
```

**Required**: `kpis[]` (each: `label`, `value`)
**Optional**: `auditChecklist[]` (each: `id`, `label`) — interactive checkboxes + progress bar

---

## 10. `riskCards` — Risk register

```json
{
  "type": "riskCards",
  "category": "Risiko",
  "title": "Risiko & Mitigasi",
  "risks": [
    {
      "no": "5.11",
      "proc": "Info ke tiap vendor terkait waktu penyelesaian",
      "risk": "Vendor lama sulit dihubungi, hutang kurang valid",
      "mit":  "BA Rekonsiliasi resmi + pembebanan proporsional"
    }
  ]
}
```

**Required**: `risks[]` (each: `no`, `proc`, `risk`, `mit`)
**Optional label overrides** (defaults shown): `clauseLabel` (`"Klausul"`), `criticalLabel` (`"Proses Kritis"`), `riskLabel` (`"Potensi Risiko Lapangan:"`), `mitigationLabel` (`"Mitigasi Preventif SOP:"`)

---

## 11. `quiz` — Mixed question types (7 available)

```json
{
  "type": "quiz",
  "category": "Uji Pemahaman",
  "title": "Uji Pemahaman",
  "lead": "Passing score 70%",
  "questions": [
    {
      "id": 1,
      "type": "mcq",
      "question": "Apa kepanjangan BAST I?",
      "options": ["Berita Acara Serah Terima I", "Berita Acara Selesai Tahap I", "Berita Acara Standar Teknis I", "Berita Acara Surat Tanda I"],
      "correctIndex": 0,
      "explanation": "BAST = Berita Acara Serah Terima."
    },
    {
      "id": 2,
      "type": "trueFalse",
      "question": "Jika PM dimutasi, hutang jadi tanggung jawab GM Ops.",
      "correctBool": true,
      "explanation": "Aturan mutasi otomatis mengalihkan tanggung jawab."
    },
    {
      "id": 3,
      "type": "fillIn",
      "question": "Apa singkatan Project Final Cost? (3 huruf)",
      "acceptedAnswers": ["PFC", "pfc"],
      "placeholder": "Ketik 3 huruf...",
      "explanation": "PFC = Project Final Cost."
    },
    {
      "id": 4,
      "type": "multipleResponse",
      "question": "Dokumen mana saja yang wajib dilampirkan?",
      "options": ["Kontrak kerja", "KTP", "Slip gaji bulan lalu"],
      "correctIndexes": [0, 1],
      "explanation": "Slip gaji bukan berkas orientasi."
    },
    {
      "id": 5,
      "type": "ordering",
      "question": "Urutkan langkah hari pertama.",
      "items": ["Pelaporan Diri", "Verifikasi Berkas", "Penerimaan Perangkat"],
      "explanation": "Administrasi mendahului perangkat."
    },
    {
      "id": 6,
      "type": "matching",
      "question": "Pasangkan pihak dengan tanggung jawabnya.",
      "pairs": [
        { "left": "HRD", "right": "Verifikasi berkas" },
        { "left": "IT", "right": "Penyiapan akun" }
      ],
      "explanation": "Satu tanggung jawab utama per pihak."
    },
    {
      "id": 7,
      "type": "numeric",
      "question": "Berapa hari kerja batas penyelesaian onboarding?",
      "answer": 3,
      "tolerance": 0,
      "unit": "hari",
      "explanation": "Tiga hari kerja pertama."
    }
  ]
}
```

**Required**: `questions[]` (each with `id`, `type` discriminator + type-specific fields)

Per-type required fields:
- `mcq`: `question`, `options[]` (≥2), `correctIndex`, `explanation`
- `trueFalse`: `question`, `correctBool`, `explanation`
- `fillIn`: `question`, `acceptedAnswers[]` (≥1), `explanation`; optional `placeholder`
- `multipleResponse`: `question`, `options[]` (≥2), `correctIndexes[]` (≥1), `explanation` — graded as an exact set: every correct index, no extras
- `ordering`: `question`, `items[]` (≥2, **listed in the correct order**), `explanation`; optional `correctOrder[]` if `items[]` is not already correct
- `matching`: `question`, `pairs[]` (≥2 × `{left, right}`), `explanation` — each pair is a correct match; the right column is shuffled for display
- `numeric`: `question`, `answer` (number), `explanation`; optional `tolerance` (absolute, default 0), `unit`, `placeholder`

Behaviour: `mcq` options are shuffled per render; `ordering` items and `matching` right-hand labels are shuffled per question; `fillIn` is compared case-insensitive + trimmed; `numeric` accepts a comma decimal (`2,5`) and applies `tolerance`.

Scoring stays binary per question (correct / not) and feeds the same percentage + pass threshold. Partial credit is deliberately not implemented — see `references/interactivity_roadmap.md`.

---

## 11b. `checkpoint` — formative in-slide practice (any slide type)

Not a slide type: an optional block you can attach to **any** of the 21 types. It renders below the
slide content, is graded immediately, and never touches the score, the attempt counter or the webhook.
When the learner answers correctly it releases the slide gate early.

```json
{
  "type": "stepByStep",
  "title": "Enam Langkah Hari Pertama",
  "steps": [ ... ],
  "checkpoint": {
    "prompt": "Susun ulang sebelum lanjut",
    "question": {
      "id": "cp-10",
      "type": "ordering",
      "question": "Urutkan empat langkah pertama hari kerja.",
      "items": ["Pelaporan Diri", "Verifikasi Berkas", "Penerimaan Perangkat", "Sesi Sambutan"],
      "explanation": "Administrasi mendahului perangkat."
    },
    "successNote": "Tepat. Administrasi memang mendahului perangkat.",
    "wrongNote": "Belum tepat — mulai dari administrasi.",
    "allowRetry": true
  }
}
```

**Required**: `checkpoint.question` (one object using the same 7 question types as `quiz`).
**Optional**: `prompt` (panel heading), `successNote`, `wrongNote`, `allowRetry` (default `true`).

Rules of use:
- It is **formative**. Do not put the same item here and in the graded quiz; the checkpoint is where
  failing is free.
- One checkpoint per slide at most. Put it immediately after the content it tests.
- A slide carrying a checkpoint counts as an *active* slide for the density guidance in
  `references/interactivity_patterns.md`, so use it to break long reading stretches.

---

## 12. `summaryCertificate` — Closing + cert trigger

```json
{
  "type": "summaryCertificate",
  "category": "Penutup & Sertifikasi",
  "title": "Penutup & Sertifikasi",
  "heroTitle": "Modul Selesai",
  "takeaways": [
    { "icon": "verified", "title": "Template-driven", "desc": "Semua konten dari JSON" },
    { "icon": "badge",    "title": "Certificate-ready", "desc": "Cetak A4 landscape" }
  ],
  "certificate": {
    "brandName": "Corporate Learning",
    "regPrefix": "CORP/LD",
    "signatory": "Director of L&D",
    "signatoryRole": "Director of L&D",
    "title": "Professional Development Module"
  },
  "failMessage": "Anda belum lulus. Silakan ulangi kuis."
}
```

**Required**: `takeaways[]` (each: `title`, `desc`)
**Conditional**: Certificate block + name/NIP inputs + "Cetak Sertifikat" button render only if `state.quizCompleted && state.quizScore >= COURSE.course.passingScore`. Of the slide-level `certificate` block, only `brandName` is read by the engine (shown in the hero meta line); signatory, certificate title and registration prefix come from the brand profile + `course.certificate`.

**Certificate configuration is course-level** (`course.certificate` in the schema). The slide-level `certificate` block above only overrides brand defaults; layout, language and page geometry live on the course:

- `template`: path (relative to `content.json`) to a custom HTML template that **replaces the inner markup of `#certificatePrintArea`**. Build-time `{{token}}` values: `judul_kursus`, `kode_kursus`, `organisasi`, `divisi`, `penandatangan`, `judul_sertifikat`, `prefix_reg`, `tanggal_cetak` (empty at build time; filled at runtime), `passing_score`, `label_kicker`, `label_presented_to`, `label_pass_note`, `label_score`, `label_pass_threshold`, `label_date`, `label_footer`, `warna_primary`, `warna_secondary`, `warna_accent`. The template **MUST** keep the five certificate contract DOM ids `certRecipientName`, `certRecipientNIP`, `certScoreVal`, `certDateVal`, `certNumberLabel`; an unknown `{{token}}` fails the build. A ready example ships at `assets/certificate.template.example.html`.
- `pageSize` (`A4 landscape` default | `A4 portrait` | `Letter landscape` | `Letter portrait`), `pageWidthMm`/`pageHeightMm`, and `printPadding` (e.g. `"0"` for full-bleed).
- `labels`: override the previously hardcoded Indonesian certificate wording (`kicker`, `presentedTo`, `passNote`, `scoreLabel`, `passThresholdNote`, `dateLabel`, `footerNote`).
- `dateLocale` (default `id-ID`) and `regNumberFormat` (default `{prefix}/{year}/{seq}`; fields `{prefix}`, `{year}`, `{seq}`; `regSequenceDigits` sets the zero padding).
- The registration number is **deterministic per participant+course+year**, so reprinting the same certificate yields the same number (it used to call `Math.random()` on every print).
- The "Ambang Batas X%" text follows `course.passingScore` — it is no longer hardcoded to 80%.

---

## 13. `imageGallery` — Photo grid / carousel (NEW)

```json
{
  "type": "imageGallery",
  "category": "Galeri",
  "title": "Foto Pelaksanaan",
  "layout": "grid",
  "columns": 3,
  "images": [
    { "src": "images/site-1.jpg", "alt": "Site photo 1", "caption": "Fase awal" },
    { "src": "images/site-2.jpg", "alt": "Site photo 2", "caption": "Fase tengah" }
  ]
}
```

**Required**: `images[]` (each: `src`, `alt`)
**Optional**: `layout` (`grid` default OR `carousel`), `columns` (2/3/4, default 3), `caption` per image

---

## 14. `videoEmbed` — YouTube / Vimeo / mp4 (NEW)

```json
{
  "type": "videoEmbed",
  "category": "Video",
  "title": "Demo Penggunaan SOP",
  "src": "https://www.youtube.com/watch?v=abc123XYZ",
  "provider": "youtube",
  "aspectRatio": "16:9",
  "durationLabel": "5:32",
  "poster": "thumbnails/demo.jpg"
}
```

**Required**: `src`, `title`
**Provider**: `youtube` (extract video ID from URL), `vimeo` (extract ID), `file` (direct mp4 — default)
**Optional**: `aspectRatio` (`16:9` default, `4:3`, `1:1`, `9:16`), `poster` (thumbnail URL), `durationLabel`

---

## 15. `calloutBox` — Info / warning / success / danger (NEW)

```json
{
  "type": "calloutBox",
  "category": "Catatan",
  "variant": "warning",
  "icon": "warning",
  "title": "Penting!",
  "body": "Pastikan seluruh <strong>13 dokumen</strong> Tutup Buku I tersedia sebelum verifikasi. Kekurangan dapat diganti dengan <em>surat pernyataan</em> bermaterai."
}
```

**Required**: `title`, `body` (HTML allowed)
**Variant values**: `info` (blue, default), `warning` (amber), `success` (emerald), `danger` (rose)
**Optional**: `icon` (Material Symbols name — defaults to variant name)

---

## 16. `stepByStep` — Numbered timeline (NEW)

```json
{
  "type": "stepByStep",
  "category": "Proses",
  "title": "5 Langkah Penerapan SOP",
  "connector": "line",
  "steps": [
    { "number": "1", "title": "Kick-off",       "desc": "Rapat awal bersama owner", "icon": "flag" },
    { "number": "2", "title": "Eksekusi",       "desc": "Pelaksanaan pekerjaan" },
    { "title":     "Verifikasi",   "desc": "Audit mutu" },
    { "title":     "BAST I",       "desc": "Serah terima fisik" },
    { "title":     "Tutup Buku I", "desc": "Penutupan akun SAP" }
  ]
}
```

**Required**: `steps[]` (each: `title` minimum; `desc`, `number` (auto-generated if absent), `icon` optional)
**Optional**: `connector` (`line` default — vertical line, `arrow` — gradient line, `none` — no connector)

---

## 17. `comparisonTable` — Tabular compare (NEW)

```json
{
  "type": "comparisonTable",
  "category": "Perbandingan",
  "title": "Tutup Buku I vs Tutup Buku II",
  "columns": [
    { "key": "aspect",   "label": "Aspek",       "icon": "info" },
    { "key": "tb1",      "label": "Tutup Buku I", "icon": "looks_one" },
    { "key": "tb2",      "label": "Tutup Buku II","icon": "looks_two" }
  ],
  "rows": [
    { "label": "Timing",   "cells": { "tb1": "Pasca BAST I",     "tb2": "Pasca BAST II" } },
    { "label": "Akun SAP", "cells": { "tb1": "Aktif untuk garansi", "tb2": "Ditutup permanen" } }
  ],
  "highlightColumn": "tb2"
}
```

**Required**: `columns[]` (each: `key`, `label`; ≥2 columns), `rows[]` (each: `cells` object keyed by column.key)
**Optional**: `highlightColumn` (column key to highlight), `row.label` (row header), `column.icon`

Cell values support HTML.

---

## 18. `faqAccordion` — Collapsible Q&A (NEW)

```json
{
  "type": "faqAccordion",
  "category": "FAQ",
  "title": "Pertanyaan Umum",
  "items": [
    { "q": "Apa itu BAST I?",  "a": "<strong>BAST I</strong> = Berita Acara Serah Terima I." },
    { "q": "Apa PFC?",         "a": "Project Final Cost. Indikator margin akhir." }
  ]
}
```

**Required**: `items[]` (each: `q`, `a` — HTML allowed in `a`)
**Optional**: per-item `icon` (defaults to "Q1", "Q2", ... number badge)

---

## 19. `hotspotImage` — Labeled graphic / find-the-target

An image with clickable pins. One renderer covers three iSpring templates: labeled graphic
(`explore`), guided image (`explore` + numbered pins), and hotspot question (`find`).

```json
{
  "type": "hotspotImage",
  "category": "Orientasi",
  "title": "Denah Hari Pertama: Empat Titik Wajib",
  "lead": "Buka setiap titik untuk tahu apa yang harus dibawa.",
  "src": "assets/denah-hari-pertama.svg",
  "alt": "Denah dengan empat area: loket pelaporan, verifikasi berkas, meja IT, ruang sambutan.",
  "caption": "Ilustrasi denah — layout sebenarnya mengikuti kantor masing-masing.",
  "mode": "explore",
  "foundLabel": "titik dibuka",
  "completeNote": "Semua titik sudah dibuka. Urutan: pelaporan → verifikasi → perangkat → sambutan.",
  "hotspots": [
    { "id": "h1", "x": 26.6, "y": 34.7, "label": "1", "title": "Loket Pelaporan",
      "body": "Lapor diri ke HC dengan membawa <strong>KTP</strong> dan surat keterangan.",
      "note": "Datang 15 menit lebih awal." },
    { "id": "h2", "x": 73.4, "y": 34.7, "label": "2", "title": "Verifikasi Berkas",
      "body": "Serahkan kontrak kerja, ijazah, dan NPWP." }
  ]
}
```

**Required**: `src`, `alt`, `hotspots[]` (each with `id`, `x`, `y`)
**Optional**: `title`, `lead`, `caption`, `mode` (`explore` default / `find`), `foundLabel`,
`completeNote`, `wrongNote`; per hotspot `label`, `title`, `body`, `note`, `correct`

Positioning: `x` and `y` are **percentages of the image** (0–100, origin top-left), so the pins scale
with the image on any screen. In `explore` mode every pin is informative and pins are numbered from
`label`. In `find` mode the learner must locate the pins marked `"correct": true`; pins without it are
decoys that show `wrongNote`.

Behaviour: formative only — opening every pin (or every correct one) shows `completeNote` and releases
the slide gate, but never touches the score, the attempt counter or the webhook. Pins are real
`<button>`s (Tab + Enter works), and the detail panel is an `aria-live` region.

Image source: a relative path, or a `data:` URI (SVG or base64 PNG) to keep the module single-file.
Sizing tip: keep the image under ~200 KB (a flat SVG is a few KB).

---

## 20. `branchingScenario` — Decision / conversation tree

Walk a tree: situation → choices → consequences → ending, with an optional debrief. This is the
`scenarioPicker` upgrade: `scenarioPicker` is one decision with two verdicts; `branchingScenario` is a
conversation with state, several branches and a retry.

```json
{
  "type": "branchingScenario",
  "category": "Studi Kasus",
  "title": "Studi Kasus: Berkas Belum Lengkap",
  "lead": "Pilih tindakan, lihat konsekuensinya.",
  "start": "n1",
  "feedbackLabel": "Konsekuensi",
  "restartLabel": "Ulangi skenario",
  "successNote": "Tepat: onboarding berjalan dan kepatuhan tetap terjaga.",
  "failureNote": "Jalur ini menunda onboarding tanpa manfaat kepatuhan.",
  "nodes": [
    {
      "id": "n1",
      "actor": "HC",
      "title": "NPWP belum diterima",
      "body": "Karyawan baru belum membawa NPWP karena masih diproses. Berkas lain lengkap.",
      "choices": [
        { "label": "Minta pulang dan kembali setelah NPWP selesai", "next": "n2",
          "correct": false, "feedback": "Keputusan ini menunda seluruh onboarding." },
        { "label": "Terima berkas, catat NPWP menyusul (14 hari)", "next": "n3",
          "correct": true, "feedback": "Onboarding tetap berjalan." }
      ]
    },
    { "id": "n2", "title": "Onboarding tertunda", "body": "...", "ending": true,
      "correct": false, "debrief": "Pisahkan verifikasi berkas dari penjadwalan onboarding." },
    { "id": "n3", "title": "Onboarding berjalan", "body": "...", "ending": true,
      "correct": true, "debrief": "Dokumen menyusul dicatat dengan tenggat agar tidak hilang." }
  ]
}
```

**Required**: `start`, `nodes[]` (each with `id`, `body`)
**Node optional**: `title`, `actor`, `choices[]`, `ending`, `correct`, `debrief`
**Choice optional**: `next` (omit on a terminal choice), `feedback`, `correct`
**Slide optional**: `title`, `lead`, `restartLabel`, `feedbackLabel`, `successNote`, `failureNote`

Rules of use:
- Every `choices[].next` must match a node `id`. The validator warns on dangling references, duplicate
  ids, dead ends (a node with no choices that is not an ending) and a missing `correct: true` ending.
- Reaching an ending marked `"correct": true` releases the slide gate. Any ending can be replayed with
  the restart button, so failing is cheap — that is the point.
- Formative: choices never score. Attach a `checkpoint` to the same slide if you also want graded
  practice on the concept.
- Keep it tight: 3–6 nodes, 2–4 choices per node. A 12-node tree nobody finishes is not a better
  scenario, it is an abandoned one.
- `actor` gives it the TalkMaster feel (the situation is spoken by HC / Atasan / Pelanggan); the
  feedback text is what makes the consequence visible instead of implied.

---

## 21. `dragDropSet` — Sort items into buckets

A pool of items and a set of buckets. **Click-to-place is the primary interaction** (select an item,
press the bucket's "place" button) because it works with keyboard, touch and screen readers; HTML5
dragging is layered on for mouse users and writes to the same state.

```json
{
  "type": "dragDropSet",
  "category": "Latihan",
  "title": "Sortir Berkas Orientasi",
  "lead": "Tempatkan setiap berkas ke kategori yang tepat.",
  "instructions": "Klik satu berkas lalu klik kategorinya. Bisa juga digeser dengan mouse.",
  "checkLabel": "Periksa penempatan",
  "resetLabel": "Acak ulang",
  "successNote": "Semua tepat: dua berkas wajib, dua boleh menyusul.",
  "partialNote": "Belum semua tepat — item merah perlu dipindahkan.",
  "buckets": [
    { "id": "wajib", "label": "Wajib hari pertama", "desc": "Lengkap sebelum onboarding." },
    { "id": "susulan", "label": "Boleh menyusul", "desc": "Dicatat dengan tenggat." }
  ],
  "items": [
    { "id": "i1", "label": "KTP", "bucket": "wajib" },
    { "id": "i2", "label": "Kontrak kerja", "bucket": "wajib" },
    { "id": "i3", "label": "NPWP", "bucket": "susulan" },
    { "id": "i4", "label": "Ijazah dilegalisir", "bucket": "susulan" }
  ]
}
```

**Required**: `buckets[]` (≥2, each `id` + `label`), `items[]` (≥2, each `id`, `label`, `bucket`)
**Optional**: `title`, `lead`, `instructions`, `checkLabel`, `resetLabel`, `successNote`,
`partialNote`; per bucket `desc`; per item `note`

Behaviour:
- Place → check → per-item right/wrong colouring + a score-free tally (`3/4 benar`). Moving any item
  clears the previous check, so the learner can iterate.
- All correct → success note + slide gate released. Formative: never touches the score, attempts or
  webhook.
- Keep it to 4–6 items and 2–3 buckets. More than that tests patience, not knowledge.
- Item labels are real buttons with 44px targets; the bucket's place button is focusable, so the whole
  exercise is operable with Tab + Enter.

---

## Choosing slide types — decision tree

When converting user's prose breakdown to slideDefs, use this guide:

1. **"Cover / pendahuluan / welcome"** → `cover`
2. **"X alasan / X poin / X definisi"** (with cards) → `cardList`
3. **"Tree / flow / swimlane / alur proses"** → `treeCanvas`
4. **"Skenario / what-if / branching"** → `scenarioPicker`
5. **"Tab A + Tab B + checklist"** → `tabbedAccordion`
6. **"Doc → PIC mapping"** → `verificationMatrix`
7. **"Compare X vs Y (2 cards)"** → `twoCardAccordion`
8. **"Dokumen / record / lampiran"** → `docTabs`
9. **"KPI / target / audit checklist"** → `kpiDashboard`
10. **"Risiko + mitigasi"** → `riskCards`
11. **"Quiz / soal / uji pemahaman"** → `quiz`
12. **"Penutup / sertifikat / summary"** → `summaryCertificate`
13. **"Galeri foto / images"** → `imageGallery`
14. **"Video / YouTube / Vimeo"** → `videoEmbed`
15. **"Catatan / peringatan / tips"** → `calloutBox`
16. **"Langkah-langkah / prosedur"** → `stepByStep`
17. **"Tabel perbandingan"** → `comparisonTable`
18. **"FAQ / pertanyaan umum"** → `faqAccordion`

When in doubt: `cardList` is the most flexible fallback for any structured content with a title + body.


---

### Type: `quiz` (Extended with Webhook Analytics)

Menampilkan kuis evaluasi pemahaman (Level 2). Mendukung MCQ, True/False, dan Fill-in-the-blank, kartu identitas peserta, batas percobaan, serta sinkronisasi otomatis nilai peserta ke Google Sheets.

#### Supported Fields:
- `type`: `"quiz"` (required)
- `title`: string judul kuis (misal: `"Uji Pemahaman Level 2"`)
- `lead`: string deskripsi singkat kuis
- `category`: string badge kategori
- `webhookUrl`: string URL Webhook Google Apps Script (opsional, jika ingin sinkronisasi analitik otomatis per-kuis — menang atas `course.webhookUrl`)
- `askParticipantInfo`: boolean (opsional, default `true`) — `false` benar-benar dihormati: kartu identitas peserta (Nama Lengkap, NIP/NRP, Jabatan, Divisi/Unit Kerja) tidak dirender, dan validasi wajib Nama/NIP di `submitQuizEvaluation()` juga dilewati.
- `questions`: array of question objects (MCQ, True/False, Fill-In)

#### Global Course Level:
- `course.webhookUrl`: URL Google Apps Script yang berlaku untuk seluruh modul jika di level slide tidak ditentukan.
- `course.passingScore`: ambang batas nilai kelulusan (default `80`).
- `course.maxQuizAttempts`: batas maksimal percobaan kuis (default `5`). Penghitung attempt tampil di header kuis; setelah limit tercapai kuis terkunci permanen.
- `course.enableGatingTimer`: `false` untuk mematikan slide gate timer (default aktif).
- `course.gatingSeconds`: durasi gate per slide dalam detik (default `10`).
- `course.devMode`: `true` untuk mode review/QA — melewati gate dan penguncian navigasi. Di-toggle saat runtime lewat badge `#previewModeBadge`.

#### Behaviour notes:
- Pengiriman ke webhook terjadi bila percobaan **lulus**, ATAU bila percobaan gagal **terakhir** sudah terpakai (attempt mencapai `course.maxQuizAttempts`). Condition engine: `state.quizPassed || state.quizAttemptCount >= maxQuizAttempts`. Percobaan gagal sebelum limit tidak dikirim; attempt terakhir yang gagal dikirim dengan `status` `"TIDAK LULUS (MAX ATTEMPT)"` (lulus → `"LULUS (>= N)"`, gagal non-final → `"REMEDIAL (< N)"`).
- Seluruh state kuis (`state.quizAttemptCount`, skor, identitas) disimpan **di memori saja** — tidak ada `localStorage`/`sessionStorage`; refresh halaman mengulang state.
- Slide `quiz` dan `summaryCertificate` otomatis **melewati** slide gate timer reguler karena memiliki gate evaluasinya sendiri.
- Sertifikat pada `summaryCertificate` hanya terbuka bila `state.quizCompleted && state.quizScore >= COURSE.course.passingScore`.
