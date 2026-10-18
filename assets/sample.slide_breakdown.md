# Sample Slide Breakdown Input

This is an example of the **structured bullets format** the skill expects from the user. The user provides this; the AI converts it to `content.json` per the schema.

For the canonical spec, see `references/input_format.md`. For per-type field reference, see `references/slide_types.md`.

---

## Slide 1: Welcome
type: cover
category: Pendahuluan
duration: 00:30
icon: info
narration: Selamat datang di modul contoh. Klik tombol Mulai Belajar untuk memulai.

heroTitle: Sample E-Learning Module
heroLead: Modul demonstrasi yang menunjukkan semua slide type yang didukung.
heroMeta: SAMPLE/MOD-001 · 2026 · Build by AI Agent
ctaLabel: Mulai Belajar
ctaIcon: play_arrow
skipTo: 1
reasons:
  - icon: verified
    title: Template-driven
    desc: Semua konten di-drive dari content.json sesuai schema.
  - icon: monitoring
    title: 21 slide types
    desc: Cover, cardList, treeCanvas, quiz, faqAccordion, dll.
  - icon: account_tree
    title: Multi-brand
    desc: 4 brand preset + custom inline. Colors auto-applied.
  - icon: badge
    title: Certificate-ready
    desc: A4 landscape print + reg number otomatis.

## Slide 2: Three Core Pillars
type: cardList
category: Konsep
duration: 02:00
icon: school
narration: Tiga pilar yang wajib dipahami sebelum lanjut ke alur proses.

title: Tiga Pilar Inti
lead: Tiga konsep yang wajib dipahami sebelum melanjutkan ke materi alur proses.
columns: 1
cards:
  - icon: looks_one
    title: Pilar 1: Definisi
    desc: Definisi resmi menentukan ruang lingkup dan ambang batas yang dipakai di seluruh modul.
    tags: [definisi, ruang-lingkup]
  - icon: looks_two
    title: Pilar 2: Proses
    desc: Proses adalah rangkaian langkah berurutan yang menghasilkan output. Tiap langkah punya PIC, input, output, dan klausul kontrak.
    tags: [proses, PIC, klausul]
  - icon: looks_3
    title: Pilar 3: Verifikasi
    desc: Verifikasi memastikan tiap output proses sudah sesuai dengan target. Indikatornya harus terukur (persentase, hari kalender, status SAP).
    tags: [verifikasi, indikator]

## Slide 3: Process Tree
type: treeCanvas
category: Alur Proses
duration: 03:00
icon: schema
narration: Tree diagram interaktif. Geser horizontal, klik node untuk lihat detail peran, input, output, dan klausul kontrak.

title: Tree Diagram Interaktif
lead: Geser horizontal, klik node untuk lihat detail (PIC, input, output, klausul).
swimlaneData:
  - section: Fase 1: Persiapan
    items:
      - id: step_1_1
        step: 1.1
        actor: PM
        actorRole: Project Manager
        title: Kick-off & Definisi Scope
        inputs: [Project Charter, Kontrak]
        outputs: [Scope Statement, Rencana Awal]
        clauses:
          - "1.1 PM memimpin rapat kick-off bersama owner."
          - "<strong>Aturan Mutasi:</strong> Jika PM dimutasi sebelum fase 1 selesai, tanggung jawab dialihkan ke GM Ops."
      - id: step_1_2
        step: 1.2
        actor: PM
        actorRole: Project Manager
        title: Penyusunan Rencana Kerja
        inputs: [Scope Statement]
        outputs: [Rencana Kerja & Jadwal (RKP)]
        clauses:
          - "1.2 RKP wajib disahkan maksimal 14 hari kalender pasca kick-off."
  - section: Fase 2: Eksekusi
    items:
      - id: step_2_1
        step: 2.1
        actor: PM
        actorRole: Project Manager
        title: Pelaksanaan Pekerjaan
        inputs: [RKP]
        outputs: [Progress Fisik 100%]
        clauses:
          - "2.1 Pekerjaan fisik dijalankan sesuai RKP. Pelaporan progres mingguan ke GM Ops."
      - id: step_decision_review
        step: KEPUTUSAN
        actor: GM
        actorRole: General Manager Operations
        title: Review Mutu
        isDecision: true
        inputs: [Progress Fisik 100%, Laporan Mutu]
        outputs: []
        clauses:
          - "Apakah hasil review mutu sesuai target BMWK3L?"
  - section: Fase 3: Penutupan
    items:
      - id: step_3_1
        step: 3.1
        actor: PM
        actorRole: Project Manager
        title: Serah Terima I (BAST I)
        inputs: [Hasil Review Mutu]
        outputs: [BA Serah Terima I]
        clauses:
          - "3.1 BAST I diterbitkan setelah owner menerima serah terima fisik."
      - id: step_3_2
        step: 3.2
        actor: SVP
        actorRole: Senior VP Operations
        title: Penutupan Akun SAP
        inputs: [BAST I]
        outputs: [Akun SAP Ditutup (Tutup Buku I)]
        clauses:
          - "3.2 SVP-OC&SCC dan SVP-FinAcc menonaktifkan akun L/R dan neraca proyek di SAP."
flowCard:
  step_1_1: { t: "Kick-off & Definisi Scope", out: "Scope Statement" }
  step_1_2: { t: "Penyusunan Rencana Kerja", out: "RKP" }
  step_2_1: { t: "Pelaksanaan Pekerjaan", out: "Progress Fisik 100%" }
  step_decision_review:
    t: "Review Mutu (Keputusan)"
    branches:
      - ["Ya (Lolos)", "Lanjut ke BAST I"]
      - ["Tidak", "Rework + re-inspeksi maksimal 14 hari"]
  step_3_1: { t: "Serah Terima I (BAST I)", out: "BA BAST I" }
  step_3_2: { t: "Penutupan Akun SAP (Tutup Buku I)", out: "Akun SAP Dinonaktifkan" }
roleFilterOptions: [Semua, PM, GM, SVP]
phaseJumps:
  - { id: fase-1, label: "Fase 1: Persiapan" }
  - { id: fase-2, label: "Fase 2: Eksekusi" }
  - { id: fase-3, label: "Fase 3: Penutupan" }

## Slide 4: FAQ
type: faqAccordion
category: FAQ
duration: 01:30
icon: help
narration: FAQ berisi pertanyaan yang sering muncul dari peserta pelatihan.

title: Pertanyaan Umum
lead: Pertanyaan yang sering muncul dari peserta pelatihan.
items:
  - q: "Apa itu BAST I dan BAST II?"
    a: "<strong>BAST I</strong> = Berita Acara Serah Terima I (serah terima fisik pekerjaan). <strong>BAST II</strong> = Berita Acara Serah Terima II (penutupan final pasca masa pemeliharaan)."
  - q: "Apa konsekuensi kalau PM dimutasi sebelum masa pemeliharaan selesai?"
    a: "Seluruh hutang pemeliharaan proyek menjadi tanggung jawab langsung <strong>GM Ops</strong>. Eskalasi otomatis, tidak perlu approval tambahan."
  - q: "Berapa ambang batas lulus uji pemahaman?"
    a: "<strong>70%</strong> untuk modul ini (default). Pass score di-set di <code>course.passingScore</code> dalam content.json."
  - q: "Apakah modul ini bisa diakses offline?"
    a: "Ya! Output HTML adalah single-file self-contained. Bisa dibuka via <code>file://</code> tanpa server."
  - q: "Bagaimana cara menambah tipe slide baru?"
    a: "Lihat <code>references/slide_types.md</code> untuk semua 21 tipe yang sudah didukung."

## Slide 5: Quiz
type: quiz
category: Uji Pemahaman
duration: 03:00
icon: quiz
narration: Uji pemahaman berisi 4 soal: 2 MCQ, 1 True/False, 1 Fill-in. Passing score 70%.

title: Uji Pemahaman
lead: "4 soal: 2 MCQ + 1 True/False + 1 Fill-in-the-blank. Passing score 70%."
questions:
  - id: 1
    type: mcq
    question: "Apa kepanjangan dari BAST I?"
    options:
      - "Berita Acara Serah Terima I (serah terima fisik pekerjaan)"
      - "Berita Acara Selesai Tahap I (tahap konstruksi)"
      - "Berita Acara Standar Teknis I (dokumen teknis)"
      - "Berita Acara Surat Tanda I (sertifikasi)"
    correctIndex: 0
    explanation: "BAST = Berita Acara Serah Terima. BAST I = serah terima fisik pekerjaan dari kontraktor ke owner."
  - id: 2
    type: trueFalse
    question: "Jika PM dimutasi sebelum masa pemeliharaan selesai, hutang pemeliharaan menjadi tanggung jawab GM Ops."
    correctBool: true
    explanation: "Aturan mutasi: PM yang dimutasi sebelum masa pemeliharaan selesai mengalihkan tanggung jawab hutang ke GM Ops secara otomatis."
  - id: 3
    type: mcq
    question: "Tipe slide mana yang dipakai untuk menampilkan diagram alur interaktif dengan hotspot detail per node?"
    options:
      - "cardList"
      - "treeCanvas"
      - "stepByStep"
      - "comparisonTable"
    correctIndex: 1
    explanation: "treeCanvas merender diagram tree dengan pan/zoom, role filter, phase jumps, dan hotspot modal per node."
  - id: 4
    type: fillIn
    question: "Apa singkatan dari Project Final Cost? (jawab dengan 3 huruf)"
    acceptedAnswers: [PFC, pfc]
    placeholder: "Ketik 3 huruf..."
    explanation: "PFC = Project Final Cost. Indikator utama margin akhir proyek. Jika >100%, wajib dibahas Komite MR dan dipaparkan ke BOD."

## Slide 6: Closing & Certificate
type: summaryCertificate
category: Penutup & Sertifikasi
duration: 00:45
icon: verified
narration: Modul selesai. Jika Anda lulus, silakan isi nama dan NIP untuk mencetak sertifikat.

title: Penutup & Sertifikasi
heroTitle: Modul Selesai
lead: Terima kasih sudah menyelesaikan modul contoh ini.
takeaways:
  - icon: verified
    title: Template-driven
    desc: Semua konten di-drive dari content.json sesuai schema.
  - icon: monitoring
    title: 21 slide types
    desc: Cover, cardList, treeCanvas, quiz, faqAccordion, dll.
  - icon: account_tree
    title: Multi-brand
    desc: Preset + custom inline. Warna auto-applied ke Tailwind config.
  - icon: badge
    title: Certificate-ready
    desc: Cetak A4 landscape dengan reg number otomatis.
certificate:
  brandName: Corporate Learning
  regPrefix: CORP/LD
  signatory: Director of Learning & Development
  signatoryRole: Director of Learning & Development
  title: Professional Development Module
failMessage: "Anda belum lulus uji pemahaman (passing score 70%). Silakan ulangi."

---

## Course meta (optional, applied to whole module)

course:
  code: SAMPLE/MOD-001
  title: Sample E-Learning Module
  effectiveDate: "Berlaku: 2026"
  logo: assets/logo.png
  logoAlt: Sample Logo
  totalUnits: 6
  passingScore: 70
  totalQuestions: 4
  devMode: true
  defaultDark: true
  enableGatingTimer: false

brand:
  preset: corporate

glossary:
  - id: term_1
    istilah: BAST I
    kategori: Operasional Kontrak
    badgeColor: "bg-blue-100 text-brand-primary dark:bg-brand-primary/20 dark:text-brand-lightBlue"
    pengertian: Berita Acara Serah Terima I — serah terima fisik pekerjaan dari kontraktor ke owner.
    catatan: Menandakan akhir masa konstruksi dan awal masa pemeliharaan.
  - id: term_2
    istilah: BAST II
    kategori: Operasional Kontrak
    badgeColor: "bg-blue-100 text-brand-primary dark:bg-brand-primary/20 dark:text-brand-lightBlue"
    pengertian: Berita Acara Serah Terima II — penutupan final pasca masa pemeliharaan selesai.
    catatan: Memicu deaktivasi permanen seluruh akun SAP L/R, neraca, dan profit center.
  - id: term_3
    istilah: PFC
    kategori: Kinerja Finansial
    badgeColor: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/60 dark:text-cyan-300"
    pengertian: Project Final Cost — rasio realisasi biaya total terhadap nilai kontrak final (NK-PPN).
    catatan: PFC > 100% = rugi. Wajib dibahas Komite MR + dipaparkan ke BOD.

tenggatCheatSheet:
  - value: "14 Hari"
    label: Ratifikasi RKP
    title: Penyusunan Rencana Kerja
    desc: Batas maksimal penyusunan + pengesahan RKP pasca kick-off.
    icon: schedule
  - value: "100%"
    label: Progress Fisik
    title: Target Penyelesaian Fisik
    desc: Ambang batas penyelesaian pekerjaan sebelum BAST I.
    icon: verified

hintTips:
  - icon: navigation
    title: Navigasi slide
    desc: Gunakan tombol Lanjut/Kembali di playbar bawah atau panah keyboard (→ / ←) untuk pindah slide.
  - icon: schema
    title: Tree diagram
    desc: Pada slide alur proses, geser horizontal dan klik node untuk lihat detail peran, input, dan outputnya.

resources:
  - icon: description
    title: Dokumen Pendukung
    desc: Dokumen yang dijadikan acuan dalam modul ini.
    items:
      - Kontrak Kerja Konstruksi
      - Project Charter
      - SOP Terkait (PP/SOP/E6-032)
  - icon: folder
    title: Template Form
    desc: Form yang dipakai dalam siklus proyek.
    items:
      - Form BAST I
      - Form BAST II
      - Form Tutup Buku I
