# Input Format: How to structure the slide breakdown

The user will provide a **slide-by-slide breakdown** of their module. This document shows the canonical structured-bullets format the skill expects, with examples.

## Why structured bullets (not prose)

Structured bullets:
- Are unambiguous — the AI parses them directly into the matching slide type
- Are predictable — the same input always produces the same output
- Catch missing fields — the AI can see "no explanation for quiz Q3" before building

Prose like "make a slide about X with some cards" leaves too much interpretation. The structured format pins down the exact type + fields per slide.

## Canonical format

The user provides one bullet block per slide, in order, following this template:

```
## Slide N: <slide title>
type: <one of 21 types from references/slide_types.md>
category: <badge text shown in meta bar>
duration: <MM:SS — shown in outline + meta bar>
icon: <Material Symbols name for sidebar outline>
narration: <transcript paragraph for CC dock + Notes tab>

<type-specific fields, indented bullets>
```

### Type-specific field blocks

Each slide type has its own expected fields. Consult `references/slide_types.md` for the full schema. Examples below use the most common types.

---

## Example 1: Minimal 3-slide module

```
## Slide 1: Welcome
type: cover
category: Pendahuluan
duration: 00:30
icon: info
narration: Selamat datang. Klik Mulai untuk memulai.

heroTitle: Welcome to the Course
heroLead: Pelajari konsep dasar dalam 3 menit.
heroMeta: SAMPLE-001 · 2026
ctaLabel: Mulai
reasons:
  - icon: verified
    title: Cepat
    desc: Selesai dalam 3 menit
  - icon: school
    title: Lengkap
    desc: Cover, konsep, quiz

## Slide 2: Three Pillars
type: cardList
category: Konsep
duration: 01:30
icon: school
narration: Tiga pilar: definisi, proses, verifikasi.

title: Three Pillars
lead: Yang wajib dipahami
columns: 1
cards:
  - icon: looks_one
    title: Definisi
    desc: Ruang lingkup + ambang batas
  - icon: looks_two
    title: Proses
    desc: Langkah berurutan + PIC
  - icon: looks_3
    title: Verifikasi
    desc: Output sesuai target

## Slide 3: Quiz
type: quiz
category: Uji Pemahaman
duration: 01:00
icon: quiz
narration: 2 soal MCQ. Passing 70%.

title: Uji Pemahaman
questions:
  - id: 1
    type: mcq
    question: Apa pilar pertama?
    options:
      - Definisi
      - Proses
      - Verifikasi
      - Audit
    correctIndex: 0
    explanation: Definisi = ruang lingkup.
  - id: 2
    type: trueFalse
    question: Verifikasi memastikan output sesuai target.
    correctBool: true
    explanation: Verifikasi = cek output vs target.
```

## Example 2: Mixed content with complex slides

```
## Slide 1: SOP Cover
type: cover
category: Pendahuluan
duration: 00:45
icon: info
heroTitle: SOP Masa Pemeliharaan
heroLead: Panduan baku pelaksanaan Tutup Buku I & II.
heroMeta: PP/SOP/C1-050 · REV-3 · Berlaku 31 Des 2024
reasons:
  - icon: verified
    title: Integrasi Standar ISO
    desc: ISO 45001:2018 + ISO 19650:2018

## Slide 2: Process Tree
type: treeCanvas
category: Alur Proses
duration: 03:00
icon: schema
narration: Klik tiap node untuk detail peran, input, output.

title: Alur Proses Penutupan
swimlaneData:
  - section: Fase 1
    items:
      - id: step_1_1
        step: 1.1
        actor: PM
        actorRole: Project Manager
        title: Kick-off
        inputs: [Project Charter]
        outputs: [Scope Statement]
        clauses:
          - "1.1 PM memimpin rapat kick-off."
  - section: Fase 2
    items:
      - id: step_2_1
        step: 2.1
        actor: PM
        actorRole: Project Manager
        title: Pelaksanaan
        inputs: [Scope Statement]
        outputs: [Progress 100%]
flowCard:
  step_1_1: { t: Kick-off, out: Scope Statement }
  step_2_1: { t: Pelaksanaan, out: Progress 100% }
roleFilterOptions: [Semua, PM, GM]
phaseJumps:
  - { id: fase-1, label: Fase 1 }
  - { id: fase-2, label: Fase 2 }

## Slide 3: FAQ
type: faqAccordion
category: FAQ
duration: 01:30
icon: help
items:
  - q: Apa itu BAST I?
    a: <strong>BAST I</strong> = serah terima fisik pekerjaan.
  - q: Apa konsekuensi PM mutasi?
    a: Hutang jadi tanggung jawab <strong>GM Ops</strong>.

## Slide 4: Closing
type: summaryCertificate
category: Penutup
duration: 00:45
icon: verified
heroTitle: Modul Selesai
takeaways:
  - icon: verified
    title: Sudah paham
    desc: 4 alasan perubahan
  - icon: schema
    title: Sudah lihat alur
    desc: Tree diagram interaktif
certificate:
  brandName: PT PP (Persero) Tbk
  regPrefix: PP/HCM-QA/C1-050
  signatory: SVP - Operation Control & SCC
```

## Rules

1. **One bullet block per slide, in order**. The order in the input = order in the final module.
2. **`type` is mandatory** and must be one of the 21 supported types.
3. **`category` is optional** but recommended — shown as the meta-bar badge.
4. **`duration` is optional** — defaults to "00:00" if absent.
5. **`icon` is optional** — defaults to "info" if absent. Use Material Symbols names.
6. **`narration` is optional** but recommended — drives the CC dock + sidebar Notes tab. When a slide has no `narration` (and no `narration["N"]` entry), the engine renders an auto "intisari" fallback in both, and `generate_audio.py` synthesises that fallback unless `--no-fallback` is passed.
7. **Type-specific fields** follow the schema in `assets/content.schema.json` + per-type examples in `references/slide_types.md`.
8. **HTML is allowed** in any free-text field (e.g., `clauses[]`, `body`, `infoBanner`, `verdict`, `a` in FAQ). Use `<strong>`, `<em>`, `<code>`, `<br>` for emphasis. Don't use `<script>` or inline event handlers (those are stripped at render time).
9. **Strings with special chars** — wrap in double quotes if they contain `:`, `{`, `}`, `[`, `]`, `,`, `#`, `&`, `*`. E.g., `heroTitle: "Welcome: Module 1"`.
10. **Arrays of objects** use YAML-style hyphen lists. **Arrays of strings** use either `[a, b, c]` flow style OR hyphen list style.
11. **Passing score and certificate config are course-level.** The quiz pass threshold is `course.passingScore` (default `80`) and the attempt limit is `course.maxQuizAttempts` (default `5`) — declare them in the optional `course:` meta block (see `assets/sample.slide_breakdown.md`). A `passingScore` placed on a `quiz` slide is rejected by the schema and never read by the engine. Certificate layout/language lives in `course.certificate` (`template`, `pageSize`, `labels`, `dateLocale`, `regNumberFormat`, …).
12. **Quiz-only slide fields**: `webhookUrl` (per-quiz webhook override) and `askParticipantInfo` — `askParticipantInfo: false` hides the participant identity card and skips the Nama/NIP required-field validation on submit.
13. **Say what the learner should *do* on each slide.** Before the JSON exists, the agent produces an **Interactivity Map** (one row per slide: class, pattern, type, why, effort) and gets it approved — see `references/interactivity_patterns.md`. If you write the breakdown yourself, mark the 2–3 places where the learner must actually decide, order, match or recall something; the rest should be plainly readable. A breakdown where every slide is a card list is complete, but it is not a course.

14. **Logo ikut folder project.** Cukup taruh `logo.png` di sebelah `content.json` (opsional `logo-dark.png`); build akan meng-inline-nya sebagai data URI. Tidak perlu menulis `course.logo`.
15. **Judul tanpa nomor dokumen.** Jangan menyalin struktur sumber ke judul (`Ketentuan Umum 6.1 s.d. 6.5`, `Poin 6.1`, `Pasal 5`). Validator menandainya; tulis judul tematik sejak awal.

## When user provides prose instead of bullets

If the user writes prose like:

> "Bikin modul 5 slide: slide 1 cover judul 'Welcome'. Slide 2 3 konsep penting dalam kartu. Slide 3 tree diagram alur 3 fase. Slide 4 quiz 5 soal campuran. Slide 5 sertifikat."

Politely ask them to provide the breakdown in the structured bullets format (give them this template), OR proceed to extract the structure yourself, showing them the resulting JSON for confirmation before building.

## Reference docs

- `references/interactivity_patterns.md` — where interaction belongs, the Interactivity Map, anti-patterns
- `references/slide_types.md` — per-type field reference for all 21 slide types
- `references/brand_profiles.md` — brand preset selection + custom brand
- `assets/content.schema.json` — formal JSON Schema for content.json
- `assets/sample.content.json` — working 21-slide example demonstrating all 21 slide types
