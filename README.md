# Modul PP 🚀
> **AI-Powered Interactive E-Learning Module Builder & Skill**  
> Ubah dokumen materi, SOP, silabus, dan slide statis menjadi aplikasi web e-learning interaktif mandiri (*single-file HTML*) berstandar industri dengan 21 tipe slide, kuis anti-spam, timer gating, dan sinkronisasi Google Sheets.

[![Live Demo](https://img.shields.io/badge/Live_Demo-WI_Pelatihan_Rev--2-success?style=for-the-badge&logo=github)](https://notsyam.github.io/wi-pelatihan-rev2/)
[![HTML5](https://img.shields.io/badge/HTML5-Single--File-E34F26?style=for-the-badge&logo=html5&logoColor=white)](#)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v3.x-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](#)
[![Web Audio API](https://img.shields.io/badge/Web_Audio-Synthesized_FX-005571?style=for-the-badge)](#)
[![Google Sheets Sync](https://img.shields.io/badge/Google_Sheets-Webhook_Sync-34A853?style=for-the-badge&logo=google-sheets&logoColor=white)](#)

---

## 🌐 Contoh Modul yang Sudah Jadi (Live Demo)

Lihat contoh modul e-learning interaktif nyata yang diproduksi menggunakan engine dan skill ini:

👉 **[Work Instruction Pelatihan (PP/SOP/E3-029 REV-2) - PT PP (Persero) Tbk](https://notsyam.github.io/wi-pelatihan-rev2/)**

> **Fitur yang dapat dicoba pada Live Demo di atas:**
> - ⏳ **Slide Gating Timer 10 Detik**: Tombol *Lanjut* terkunci dengan hitung mundur di setiap slide baru.
> - 🌲 **Interactive Flowchart Canvas**: Diagram pohon alur kerja dengan pan/zoom, filter peran (*Role Filter*), dan hotspot interaktif.
> - 📝 **Native In-App Quiz**: Uji pemahaman dengan kartu identitas peserta, acak opsi, dan batas maksimal 5 kali percobaan.
> - 🎓 **Official Printable Certificate**: Membuka gembok sertifikat resmi berformat cetak A4 landscape ke PDF jika lulus kuis ($\ge 80$).
> - 📊 **Real-time Webhook Sync**: Pengiriman skor otomatis ke Google Sheets dengan pencegahan data spam dan upsert nilai tertinggi.

---

## 📖 Ringkasan (Overview)

**Modul PP** adalah skill AI agent dan builder engine yang mengonversi dokumen kurikulum, modul training, SOP kerja, serta slide statis menjadi modul e-learning interaktif yang modern, responsif, dan siap produksi.

Hasil akhir berupa **satu file `.html` mandiri (standalone)** yang dapat langsung dibuka di browser tanpa server lokal (`file://`), di-host di static web hosting (GitHub Pages, Vercel, Netlify), maupun disematkan ke dalam LMS (Moodle, Canvas, Blackboard) via iframe atau SCORM package.

---

## 🚀 Cara Menggunakan (Usage Guide)

Kekuatan utama dari skill **Modul PP** adalah kemudahannya: **Anda TIDAK perlu menulis kode JSON rumit atau konfigurasi teknis yang panjang.**

Cukup lampirkan dokumen materi asli (PDF/Word/SOP) dan berikan **daftar outline topik sederhana**, AI Agent yang ditenagai skill ini akan otomatis menganalisis isi dokumen, memilih tipe slide interaktif yang paling cocok (flowchart, kartu, matriks, kuis, sertifikat), dan mengompilasinya menjadi modul web interaktif siap pakai.

---

### Alur 1: Input Nyata Pengguna (Sederhana & Cepat) 🔥

Berikut adalah contoh teks prompt yang benar-benar digunakan untuk memproduksi modul **[Work Instruction Pelatihan Rev-2](https://notsyam.github.io/wi-pelatihan-rev2/)**:

#### 📄 Prompt Input Pengguna:
> *"Tolong buatkan modul e-learning interaktif dari dokumen SOP Pelatihan terlampir (PDF) dengan susunan berikut:*
> 
> *Catatan: Menu Terminologi berada di samping Hint/Navigasi berisikan Definisi yang ada di Poin 4.*  
> 
> - *Halaman 0 : Pendahuluan*  
> - *1 : Maksud dan Tujuan, Ruang Lingkup*  
> - *2 : Referensi*  
> - *3 : Alur Proses 5.1 Learning Needs Diagnostic*  
> - *4 : Alur Proses 5.2 Learning Design & Development*  
> - *5 : Alur Proses 5.3 Learning Delivery & Deployment*  
> - *6 : Alur Proses 5.4 Learning Impact Measurement*  
> - *7 : Ketentuan Umum 6.1.1 sampai 6.1.3*  
> - *8 : Ketentuan Umum 6.2.1 sampai 6.2.6*  
> - *9 : Ketentuan Umum 6.3.1 sampai 6.3.6*  
> - *10 : Ketentuan Umum 6.4.1 sampai 6.4.4*  
> - *11 : Dokumen Terkait*  
> - *12 : Record*  
> - *13 : Lampiran*  
> - *14 : Performance Measurement*  
> - *15 : Identifikasi Potential Risk*  
> - *16 : Kuis 10 Soal*  
> - *17 : Penutup & Sertifikat"*

#### 🧠 Apa yang Dilakukan AI Agent (Skill Engine) Secara Otomatis:
1. **Membaca Dokumen Sumber (PDF/Word)** secara mendalam.
2. **Pemetaan Cerdas ke 21 Tipe Slide**:
   - Poin 0 $\rightarrow$ `cover` (Hero title, nomor SOP, badge tanggal berlaku, CTA mulai).
   - Poin 1 & 2 $\rightarrow$ `cardList` / `twoCardAccordion` (Maksud, tujuan, ruang lingkup).
   - Poin 3–6 (Alur Proses) $\rightarrow$ `treeCanvas` (Flowchart canvas interaktif, filter peran pelaksana, hotspot modal).
   - Poin 7–10 (Ketentuan Umum) $\rightarrow$ `tabbedAccordion` (Pemisahan tab terstruktur agar materi nyaman dibaca).
   - Poin 11–13 $\rightarrow$ `docTabs` / `verificationMatrix` (Daftar dokumen & formulir terkontrol).
   - Poin 14 $\rightarrow$ `kpiDashboard` (Metrik kuantitatif & target evaluasi).
   - Poin 15 $\rightarrow$ `riskCards` (Identifikasi risiko & mitigasi operasional).
   - Poin 16 $\rightarrow$ `quiz` (10 soal evaluasi dengan identitas peserta, acak opsi & batas 5 attempt).
   - Poin 17 $\rightarrow$ `summaryCertificate` (Generator sertifikat resmi A4 landscape).
3. **Mengekstrak Terminologi (Poin 4)** ke dalam modal glossary interaktif.
4. **Menerapkan Gate Timer 10 Detik** di setiap slide dan integrasi webhook Google Sheets.
5. **Mengompilasi** menjadi satu file `index.html` mandiri tanpa dependensi luar!

---

### Alur 2: Format Structured Bullets (Bagi yang Ingin Kontrol Granular)

Jika Anda tidak melampirkan dokumen PDF atau ingin menentukan sendiri teks setiap kartu/tombol secara eksplisit, Anda dapat menggunakan format **Structured Bullets**:

#### 📋 Template Standar Per Slide:
```markdown
## Slide <Nomor>: <Judul Slide>
type: <tipe_slide>              # Pilih dari 21 tipe slide yang tersedia
category: <Kategori Badge>      # Ditampilkan di stage bar atas (misal: Pendahuluan, Prosedur, Evaluasi)
duration: <MM:SS>               # Estimasi durasi membaca (misal: 01:30)
icon: <nama_material_icon>      # Ikon Google Material Symbol untuk sidebar menu
narration: <Naskah Suara>       # Teks narasi untuk Closed Caption (CC) dan tab Catatan

<Field khusus sesuai tipe slide, format YAML/indented bullets>
```

---

#### 💡 Contoh Nyata Input Teks Breakdown Materi:

```markdown
# Breakdown Modul: Prosedur Pengajuan Cuti Karyawan (SOP-HC-004)

## Slide 1: Tata Cara Pengajuan Cuti
type: cover
category: Pendahuluan
duration: 00:30
icon: verified_user
narration: Selamat datang pada modul interaktif pengajuan cuti tahunan dan khusus karyawan.
heroTitle: Prosedur Pengajuan Cuti Karyawan
heroLead: Panduan standar operasional pengajuan, verifikasi, dan persetujuan cuti.
heroMeta: SOP-HC-004 · Revisi 2 · Berlaku 2026
ctaLabel: Mulai Belajar
reasons:
  - icon: schedule
    title: Tepat Waktu
    desc: Pengajuan minimal H-3 sebelum tanggal pelaksanaan cuti.
  - icon: approval
    title: Alur Berjenjang
    desc: Persetujuan Atasan Langsung hingga Manager HRD.

## Slide 2: Jenis Hak Cuti Karyawan
type: cardList
category: Materi Pokok
duration: 01:30
icon: category
narration: Kenali tiga kategori hak cuti yang berlaku di perusahaan.
title: 3 Kategori Hak Cuti
lead: Pelajari ketentuan dan kuota masing-masing cuti berikut
columns: 3
cards:
  - icon: event_available
    title: Cuti Tahunan
    desc: Hak 12 hari kerja per tahun setelah masa kerja minimal 12 bulan berturut-turut.
  - icon: medical_services
    title: Cuti Sakit
    desc: Wajib melampirkan surat keterangan dokter resmi jika melebihi 1 hari kerja.
  - icon: celebration
    title: Cuti Khusus / Ibadah
    desc: Termasuk cuti menikah (3 hari), melahirkan (3 bulan), dan ibadah haji.

## Slide 3: Alur Verifikasi & Persetujuan
type: stepByStep
category: Prosedur
duration: 02:00
icon: linear_scale
narration: Ikuti 4 tahapan berurutan pengajuan cuti melalui portal HC.
title: 4 Langkah Pengajuan di Portal HRIS
steps:
  - step: 1
    title: Input Pengajuan di HRIS
    desc: Karyawan login ke portal dan mengisi tanggal serta alasan cuti.
  - step: 2
    title: Review Atasan Langsung
    desc: Atasan memeriksa sisa kuota dan jadwal operasional tim kerja.
  - step: 3
    title: Persetujuan HRD
    desc: Tim HR memvalidasi eligibilitas dan menerbitkan notifikasi persetujuan.
  - step: 4
    title: Notifikasi Otomatis
    desc: Surat izin cuti elektronik dikirimkan ke email karyawan dan atasan.

## Slide 4: Simulasi Pengambilan Keputusan
type: scenarioPicker
category: Studi Kasus
duration: 02:00
icon: psych
narration: Uji pemahaman Anda terhadap kasus darurat di lapangan.
title: Dilema Cuti Mendadak
scenario: Karyawan A mengalami musibah darurat keluarga pada hari H kerja dan belum sempat mengajukan di portal. Apa langkah yang tepat?
options:
  - label: A. Menunggu masuk kerja baru mengurus izin cuti seminggu kemudian.
    isCorrect: false
    feedback: Kurang tepat. Karyawan wajib segera memberi kabar kepada atasan langsung di hari yang sama.
  - label: B. Memberitahu atasan via telepon/pesan hari itu juga, lalu input form HRIS maksimal H+1 masuk kerja.
    isCorrect: true
    feedback: Benar! Prosedur darurat memperbolehkan pelaporan verbal terlebih dahulu diikuti input administratif resmi.

## Slide 5: Uji Pemahaman (Quiz)
type: quiz
category: Evaluasi
duration: 03:00
icon: quiz
narration: Jawab 2 pertanyaan berikut untuk menguji pemahaman Anda. Syarat kelulusan minimal 80.
title: Evaluasi Pemahaman Kuis
questions:
  - id: 1
    type: mcq
    question: Berapa hari batas minimal pengajuan cuti tahunan normal sebelum tanggal pelaksanaan?
    options:
      - H-1 hari kerja
      - H-3 hari kerja
      - H-7 hari kerja
      - Hari H keberangkatan
    correctIndex: 1
    explanation: Sesuai SOP, pengajuan normal wajib dilakukan minimal H-3 agar atasan dapat mengatur jadwal tugas tim.
  - id: 2
    type: trueFalse
    question: Cuti sakit selama lebih dari 1 hari wajib disertai surat keterangan dokter resmi.
    correctBool: true
    explanation: Surat dokter resmi diperlukan untuk validasi absensi medis berbayar.

## Slide 6: Rangkuman & Sertifikat
type: summaryCertificate
category: Penutup
duration: 00:30
icon: workspace_premium
narration: Selamat! Anda telah menyelesaikan seluruh rangkaian materi dan lulus evaluasi.
title: Sertifikat Kompetensi
certificate:
  brandName: "PT PP (Persero) Tbk — Human Capital"
takeaways:
  - "Pengajuan cuti tahunan dilakukan minimal H-3 via portal HRIS."
  - "Kondisi darurat wajib dilaporkan di hari yang sama kepada atasan langsung."
  - "Sertifikat resmi diterbitkan otomatis setelah lulus kuis dengan skor >= 80."
```

> **Catatan**: `passingScore` bukan field slide — ambang kelulusan ditetapkan di level kursus (`course.passingScore`, default `80`). Menaruh `passingScore` di dalam slide ditolak oleh skema dan tidak pernah dibaca engine. Dari blok `certificate` pada slide, engine hanya membaca `brandName`; penandatangan, judul sertifikat, dan prefix registrasi berasal dari brand profile + `course.certificate`.

---

### Alur 3: Kompilasi Manual Menggunakan CLI Python

Jika Anda memiliki data dalam format JSON (`kursus.json`):

1. **Validasi Skema**:
   ```bash
   python scripts/validate_content.py kursus.json
   ```
2. **Produksi Audio Narasi Edge-TTS (Opsional tapi Direkomendasikan)**:
   ```bash
   python scripts/generate_audio.py \
     --content kursus.json \
     --output-dir dist/audio \
     --voice ardi \
     --rate -4%
   ```
   *Naskah per slide diresolusi berurutan: `slides[N].narration` → `narration["N"]` → fallback otomatis "intisari" yang disusun dari title/lead/desc/steps/takeaways slide itu sendiri; slide tanpa naskah sama sekali dilaporkan dan dilewati. Safe HTML/Markdown dibersihkan sebelum sintesis, lalu kamus pelafalan (`PRONUNCIATION_MAP`: SOP→"es o pe", BUMN, PT PP, HRIS, KPI, PIC, dll.) diterapkan — tambah entri proyek via `--pronunciation-file <json>` atau matikan dengan `--no-phonetic`. MP3 dinamai `unit_<slideIndex>.mp3` di dalam `--output-dir`. Flag lain: `--check` (laporan coverage saja), `--dry-run` (cetak naskah final tanpa TTS), `--force` (timpa MP3 yang sudah ada), `--unit N` (satu slide saja), `--no-fallback`.*

3. **Kompilasi ke HTML Mandiri**:
   ```bash
   python scripts/build_module.py \
     --content kursus.json \
     --output dist/kursus_interaktif.html \
     --validate
   ```
   *Path output adalah apa pun yang Anda berikan ke `--output` (konvensi yang disarankan: `<project-dir>/index.html`) — tidak ada direktori `download/` khusus. Skrip mendukung Rich Text (Safe HTML: `<strong>`, `<br>`, `<em>` serta Markdown: `**bold**`, `*italic*`, `\n`) secara otomatis tanpa merusak simbol pembanding matematika.*

4. **Jalankan Verification Gate (Wajib)**:
   ```bash
   python scripts/validate_content.py kursus.json
   python tools/verify_module.py dist/kursus_interaktif.html --content kursus.json
   ```
   *`validate_content.py` tidak membutuhkan dependensi pihak ketiga — `jsonschema` dipakai bila kebetulan terpasang, jika tidak ada validator bawaan yang menangani subset JSON Schema yang dipakai skema. Error slide kini dilaporkan **presisi** per tipe: field wajib yang hilang, properti tambahan tak dikenal, atau tipe slide tak dikenal dengan saran (mis. "Did you mean 'comparisonTable'?") alih-alih `matches 0 of 21 allowed schemas`. Validator juga menjalankan advisory semantik: `correctIndex` di luar rentang opsi, id soal duplikat, `acceptedAnswers` kosong, `units[].duration` bukan MM:SS, `course.totalQuestions` tidak cocok, coverage narasi, `course.certificate.template` hilang, dan preset `custom` tanpa warna — plus peringatan bahwa `passingScore` di level slide **tidak dibaca engine**. Advisory dicetak ke stderr dan **tidak** mengubah exit code kecuali dengan `--strict`; `--quiet` menahan advisory.*
   *`tools/verify_module.py` adalah quality gate offline (butuh Node.js di PATH) yang memeriksa keseimbangan tag DOM statis, sintaks setiap blok `<script>` via `node --check`, DOM id wajib, text node `>` nyasar, fungsi `SLIDE_RENDERERS` yang terdefinisi — dan cakupan registri yang persis sama dengan tipe slide di skema — placeholder build yang belum terisi, injeksi literal `COURSE`, serta lima DOM id kontrak sertifikat (`certRecipientName`, `certRecipientNIP`, `certScoreVal`, `certDateVal`, `certNumberLabel`). Dengan `--content kursus.json` gate juga membandingkan literal `COURSE` yang diinjeksi dengan `content.json` byte-per-byte untuk mendeteksi build basi. Panggilan `alert()`/`confirm()` native dilaporkan sebagai advisory. **Keduanya harus lolos sebelum modul dinyatakan sukses.***

5. Buka file `dist/kursus_interaktif.html` di browser Anda!

---

## ✨ Fitur Teknis & Arsitektur Keamanan

### 1. ⏱️ 10-Second Slide Gating Timer
- Dikonfigurasi lewat `course.enableGatingTimer` (default aktif) dan `course.gatingSeconds` (default `10`).
- Tombol **Lanjut (Next)** (`#btnNextSlide`) otomatis terkunci (`disabled`) selama 10 detik saat slide baru dibuka, lengkap dengan hitung mundur dinamis (`Tunggu (10s)` $\rightarrow$ `Tunggu (1s)`).
- Badge `#slideGateNotice` di bar durasi atas menampilkan countdown amber (`⏳ Selesaikan materi dalam Xs...`), lalu berubah menjadi emerald **`Selesai Dipelajari`** saat gate tuntas.
- Notifikasi peringatan jika user mencoba melompat lewat daftar isi/sidebar sebelum timer selesai: `Mohon pelajari materi ini terlebih dahulu. Anda dapat lanjut dalam X detik.`
- Dilengkapi efek *unlock chime* (Web Audio) dan animasi pulse glow (`btn-next-ready`) saat waktu tuntas.
- **Dikecualikan** untuk slide kuis & sertifikat, serta slide yang sudah tuntas dipelajari (tidak dikunci ulang saat dibuka kembali).

### 2. 📝 Native In-App Quiz & Anti-Spam (Maksimal 5 Attempt)
- **Kartu identitas peserta tampil di halaman kuis** (bukan di halaman sertifikat): Nama Lengkap, NIP/NRP, Jabatan, dan Divisi/Unit Kerja.
- Mendukung **7 tipe soal** — MCQ, Benar/Salah, Isian Singkat, **multiple-response, ordering, matching, numeric** — dengan pengacakan opsi/urutan, toleransi angka, dan pembahasan kunci jawaban.
- **`checkpoint` (formatif, di slide mana pun)**: blok latihan opsional di bawah materi yang langsung diperiksa, boleh dicoba lagi, **tidak** menambah skor/attempt dan tidak mengirim webhook; jawaban benar hanya mempercepat terbukanya gate slide. Lihat `references/slide_types.md` §11b + `references/interactivity_patterns.md`.
- **Batas Percobaan**: Maksimal 5 kali percobaan kuis (`course.maxQuizAttempts: 5`). Penghitung attempt tampil di header kuis, dan tombol ulangi menunjukkan sisa percobaan (`Ulangi Kuis (Sisa X Percobaan)`).
- **Gating Kelulusan**:
  - Skor $\ge 80$: Membuka gembok halaman Sertifikat Resmi, selebrasi konfeti, dan pengiriman nilai ke server analitik.
  - Skor $< 80$ & Attempt $< 5$: Menampilkan evaluasi remedial dan tombol ulangi kuis. Percobaan gagal **belum dikirim** ke sheet untuk mencegah polusi data; hanya attempt terakhir yang tetap dikirim.
  - Skor $< 80$ & Attempt $= 5$: Kuis terkunci permanen (tombol ulangi `disabled`) dengan pesan `Kesempatan kuis Anda telah habis (5/5). Silakan hubungi Tim HC / PIC Pelatihan untuk evaluasi lebih lanjut.`

### 3. 📊 Google Sheets Serverless Webhook Sync (Upsert Nilai Tertinggi)
- Endpoint serverless gratis menggunakan Google Apps Script (GAS).
- Pengiriman dilakukan engine melalui `fetch(webhookUrl, {method: 'POST', body: JSON.stringify({...})})` saat kuis **lulus** atau saat **percobaan terakhir gagal** (attempt mencapai `course.maxQuizAttempts`). Condition engine: `state.quizPassed || state.quizAttemptCount >= maxQuizAttempts`; status yang dikirim `LULUS (>= N)`, `TIDAK LULUS (MAX ATTEMPT)`, atau `REMEDIAL (< N)`.
- URL webhook dapat dikonfigurasi per-slide (`webhookUrl` pada slide kuis, diprioritaskan) atau untuk seluruh modul (`course.webhookUrl`).
- **Aman Beban Serentak**: Menggunakan `LockService.getScriptLock()` untuk menangani antrean pengiriman 50+ peserta secara bersamaan tanpa *race condition*.
- **Mekanisme Upsert**: Jika NIP sudah tercatat, data baris lama **hanya ditimpa jika nilai baru lebih tinggi** dari nilai sebelumnya.
- Seluruh state engine (skor, attempt, gate, identitas) disimpan **di memori saja** — tidak ada `localStorage`/`sessionStorage`. Refresh halaman akan mengulang state dari awal.
- Panduan setup lengkap: [`references/gas_webhook_setup.md`](references/gas_webhook_setup.md).

### 4. 🧩 21 Tipe Slide Interaktif
1. `cover`: Hero title, badge versi, deskripsi, dan CTA mulai.
2. `cardList`: Kartu interaktif grid dengan icon, detail modal, dan status.
3. `treeCanvas`: Alur proses flowchart interaktif dengan zoom/pan, filter peran (*Role Filter*), dan modal hotspot.
4. `scenarioPicker`: Simulasi pengambilan keputusan / dilema etika dengan umpan balik instan.
5. `tabbedAccordion`: Navigasi tab konten berbasis pilar/tahapan.
6. `verificationMatrix`: Matriks verifikasi dokumen dengan status lulus/tinjau.
7. `twoCardAccordion`: Komparasi 2 kartu interaktif (*sebelum vs sesudah, do vs don't*).
8. `docTabs`: Tampilan dokumen acuan/formulir resmi dengan tab berkas.
9. `kpiDashboard`: Dashboard metriks kuantitatif dengan indikator pencapaian.
10. `riskCards`: Matriks evaluasi risiko dengan mitigasi operasional.
11. `quiz`: Mesin kuis komprehensif dengan grading instan.
12. `summaryCertificate`: Rangkuman poin kunci + generator sertifikat resmi siap cetak A4 landscape ke PDF.
13. `imageGallery`: Galeri visual dokumentasi.
14. `videoEmbed`: Pemutar video terintegrasi dengan caption.
15. `calloutBox`: Kotak peringatan/peringatan kepatuhan penting.
16. `stepByStep`: Prosedur langkah demi langkah sekuensial.
17. `comparisonTable`: Tabel komparasi multi-kolom responsif.
18. `faqAccordion`: Tanya jawab interaktif.
19. `hotspotImage`: Gambar dengan titik interaktif — *labeled graphic* (mode `explore`) atau latihan mencari target (mode `find`), lengkap dengan progres dan umpan balik.
20. `branchingScenario`: Pohon keputusan/percakapan gaya *TalkMaster* — pilihan bercabang, umpan balik per pilihan, ending + debrief, bisa diulang.
21. `dragDropSet`: Sortir item ke kategori — klik-untuk-menempatkan (keyboard & sentuh) dengan drag mouse sebagai tambahan, plus pemeriksaan formatif.

### 4b. 🖼️ Logo Otomatis & Layout Kartu Seimbang
- **Logo self-contained**: taruh `logo.png` (atau `.jpg/.svg/.webp`) di sebelah `content.json` — build otomatis meng-inline sebagai data URI, jadi modul tetap satu file tanpa folder aset. Opsional `logo-dark.png` untuk aset dark-mode khusus; tanpa itu logo tunggal dirender sebagai silhouette putih di dark mode. Kalau tidak ada file sama sekali, header menampilkan **monogram** dari nama brand, bukan gambar rusak.
- **Kartu ganjil tetap seimbang**: grid kartu (`.cardgrid`) memusatkan baris terakhir, sehingga jumlah kartu ganjil tidak meninggalkan ruang kosong di satu sisi. Berlaku untuk `cardList`, `imageGallery`, `kpiDashboard`, `docTabs`, dan daftar takeaways.
- **Linter judul**: `validate_content.py` menandai judul yang masih membawa nomor dokumen (`Poin 6.1`, `Pasal 5`, `Lampiran III`, `6.1.2`, rentang `s.d.`) supaya judul ditulis tematik.

### 5. 🎨 UI Parity, Multi-Brand Presets & Dark/Light Mode

Modul yang dihasilkan **wajib secara visual selaras** dengan *design system* pada `upstream/index_tree_canvas.html` — ini merupakan persyaratan utama (bukan opsional).

- **Palet wajib**: biru/putih korporat yang ketat — primary `#2B73BD`, primaryHover `#205c99`, secondary `#5A89B8`, secondaryLight `#7eabd9`, accent lightBlue `#38BDF8`, kanvas terang iceBg `#F0F4F7`, surface putih, kanvas gelap `#09111E`, dark surface `#111C2E`, dark border `#1F2F4A`, dark subtle `#16233B`. **Tidak boleh ada aksen cokelat/beige/tan.**
- **Font**: Plus Jakarta Sans (sans), JetBrains Mono (mono). Tema default adalah **dark** (`darkMode: 'class'`).
- **Anatomi player**: top player bar (logo, kode kursus, tanggal berlaku, modal Terminologi/Tenggat/Petunjuk, toggle tema, fullscreen) → sidebar *off-canvas* yang bisa dilipat di mobile dengan tab Menu / Transkrip / Lampiran → stage viewport terpusat → bottom playbar (play/pause, replay, timecode, seekbar, toggle CC, kecepatan, penghitung slide, prev/next) → caption dock.
- **Touch target interaktif harus ≥44px**; jangan pernah menggabungkan `line-clamp-*` dengan `overflow-y-auto`; chevron di dalam `<summary>` perlu `shrink-0`.
- **Logo hanya muncul di `#topHeader`**, memakai PNG transparan dengan `dark:brightness-0 dark:invert`.

**Preset brand.** Preset default adalah **`ptpp`**, karena hanya preset itulah yang membawa palet persis dari modul referensi. `scripts/build_module.py` juga sudah default ke `"ptpp"`.

> Memilih `corporate` / `education` / `tech-startup` berarti **secara sengaja mengganti palet** dan karenanya **menyimpang dari UI referensi**. Hanya `ptpp` — atau `custom` dengan nilai hex persis di atas — yang memenuhi syarat parity. (Contoh: `corporate` memakai biru berbeda, `primary 0F4C81`.)

Toggle instan Dark / Light mode. Kontras **tidak** dijamin WCAG AA menyeluruh: `scripts/build_module.py` mencetak CONTRAST ADVISORY ke stderr bila token brand di bawah 4.5:1 terhadap teks putih. Dengan preset bawaan `ptpp`, `primary`/`primaryHover` lolos, tetapi `secondary` (3.68:1) dan `accent` (2.14:1) tidak — pakai keduanya hanya untuk elemen tanpa teks putih. Animasi konfeti/pulse juga belum menghormati `prefers-reduced-motion`.

### 6. 🎓 Sertifikat, SCORM Runtime & Dev Mode
- **Cetak Sertifikat**: tombol "Cetak Sertifikat" hanya terbuka setelah kuis lulus; engine mengisi `#certificatePrintArea` (nama organisasi, penandatangan, nomor registrasi, tanggal, nama + NIP peserta) lalu memanggil `window.print()` — geometri halaman mengikuti aturan `@media print` + `course.certificate` (default A4 landscape). Nomor registrasi kini **deterministik per peserta+kursus+tahun**, jadi cetak ulang menghasilkan nomor yang sama (sebelumnya `Math.random()` tiap klik cetak).
- **Kustomisasi Sertifikat (`course.certificate`)**: `template` (path HTML relatif ke `content.json`) menggantikan markup dalam `#certificatePrintArea` dan mendukung token build-time (`judul_kursus`, `kode_kursus`, `organisasi`, `divisi`, `penandatangan`, `judul_sertifikat`, `prefix_reg`, `passing_score`, `label_kicker`, `label_presented_to`, `label_pass_note`, `label_score`, `label_pass_threshold`, `label_date`, `label_footer`, `warna_primary`, `warna_secondary`, `warna_accent`); template **wajib** mempertahankan lima DOM id kontrak sertifikat, dan `{{token}}` tak dikenal menggagalkan build. Contoh siap pakai: `assets/certificate.template.example.html`.
- **Geometri & bahasa sertifikat**: `pageSize` (`A4 landscape` default, `A4 portrait`, `Letter landscape`, `Letter portrait`), `pageWidthMm`/`pageHeightMm`, `printPadding` (mis. `"0"` untuk full-bleed), `labels` (menimpa teks sertifikat bawaan), `dateLocale` (default `id-ID`), dan `regNumberFormat` (default `{prefix}/{year}/{seq}`; `regSequenceDigits` mengatur padding nol). Teks "Ambang Batas X%" mengikuti `course.passingScore`, tidak lagi hardcoded 80%.
- **Preview sertifikat tanpa lulus kuis**: buka modul dengan hash `#cert-preview` di URL (mis. `file:///.../index.html#cert-preview`). Engine mengisi data peserta contoh, menampilkan `#certificatePrintArea` pada ukuran halaman sebenarnya di atas player, dan menampilkan badge yang bisa ditutup — tekan `Ctrl+P` untuk melihat persis hasil cetaknya. Loop desain tercepat: edit template → build ulang → refresh dengan `#cert-preview`. Preview dan cetak memakai fungsi `fillCertificate()` yang sama, jadi tidak mungkin berbeda.
- **Template contoh**: `assets/certificate.template.example.html` (kartu portrait) dan `assets/certificate.template.modern.html` (landscape full-bleed, panel navy + area peserta).
- **SCORM Runtime**: fungsi `findSCORMAPI` / `initSCORM` / `recordSCORMProgress` / `finishSCORM` berkomunikasi dengan SCORM API LMS bila modul dijalankan di dalam SCORM player (no-op di browser biasa). Paketkan modul dengan `scripts/package_scorm.py`:
  ```bash
  python scripts/package_scorm.py --html dist/modul.html --output dist/modul_scorm.zip
  ```
- **Badge Dev/Review (`#previewModeBadge`)**: mengubah `COURSE.course.devMode` saat runtime — `false` untuk navigasi produksi yang tergerbang, `true` untuk navigasi bebas saat review/QA.
- **Verification Gate**: `tools/verify_module.py` memvalidasi DOM, sintaks JS, DOM id wajib (termasuk kontrak sertifikat), registri `SLIDE_RENDERERS`, placeholder build, dan injeksi `COURSE` sebelum modul dinyatakan lolos.

---

## 📁 Struktur Repositori

```text
modul-pp/
├── SKILL.md                          # Spesifikasi AI Agent Skill (Antigravity, Gemini, Claude)
├── README.md                         # Dokumentasi lengkap repositori
├── assets/                           # shell.template.html, content.schema.json, brand.profiles.json,
│                                     # sample.content.json, sample.slide_breakdown.md,
│                                     # certificate.template.example.html
├── scripts/                          # build_module.py, validate_content.py, generate_audio.py,
│                                     # package_scorm.py, smoke_test_module.py, self_check.py
├── references/                       # slide_types.md, input_format.md, brand_profiles.md,
│                                     # pedagogical_patterns.md, gas_webhook_setup.md, engine_behaviour.md
├── tools/
│   ├── verify_module.py              # Quality gate offline (DOM + sintaks JS, butuh Node.js)
│   └── sync_installs.py              # Mirror antar-installasi skill + verifikasi SHA256
├── dsh-command/                      # Plugin slash command DSH (/modul-pp) — paket terpisah
└── upstream/
    └── index_tree_canvas.html        # Design reference (modul PT PP SOP) — pinned, READ-ONLY
```

> **`assets/shell.template.html` adalah engine kanonik.** File ini dipelihara langsung dan **tidak lagi di-generate**. Skrip lama `scripts/build_shell_template.py` sudah **dihapus**, karena shell yang dikirim telah menyimpang **617 baris lebih maju** dari yang bisa dihasilkan generator — menjalankannya akan diam-diam menghancurkan slide gate timer, SCORM runtime, kartu identitas peserta, batas 5 percobaan, dan webhook Google Sheets. Edit shell secara langsung, lalu **selalu jalankan `python scripts/self_check.py`** (gate regresi skill) dan ulangi verification gate pada modul hasil build.
>
> **`upstream/index_tree_canvas.html` adalah design reference** (modul PT PP SOP versi final). Jangan diubah — bahasa visual shell harus tetap setia padanya.
>
> **`scripts/self_check.py` adalah gate regresi skill itu sendiri**: `python scripts/self_check.py` menjalankan 14 check (validasi skema sample, build, verification gate dengan parity `COURSE`, regresi tabrakan token palet, preservasi hex literal author, kontrak placeholder, template sertifikat kustom, pipeline narasi termasuk respelling fonetis, dan regenerasi + verifikasi `test_build.html`). Tambahkan `--with-smoke` untuk pass Playwright. Jalankan setiap kali `assets/shell.template.html` diedit.
>
> **Skill ini terpasang di beberapa lokasi** (`~/.dsh/skills/modul-pp`, `~/.gemini/config/skills/modul-pp`, dan salinan di workspace). Pilih **satu salinan kanonik** dan perlakukan sisanya sebagai mirror hasil deploy — setiap edit harus disinkronkan (mis. lewat `tools/sync_installs.py`), bukan diedit langsung di banyak tempat.

---

## 🛠️ Integrasi Google Apps Script (Webhook Nilai)

Untuk mencatat hasil nilai peserta secara terpusat ke spreadsheet Google:
1. Buat Google Sheet dengan header kolom:
   `Timestamp | Nama | NIP | Jabatan | Divisi | Skor | Status | Attempt`
2. Buka **Extensions > Apps Script**, masukkan template kode dari [`references/gas_webhook_setup.md`](references/gas_webhook_setup.md).
3. Deploy sebagai **Web App** dengan akses `Anyone`.
4. Masukkan URL hasil deployment ke konfigurasi modul e-learning Anda.

---

## 📄 Lisensi
Proyek ini didistribusikan di bawah lisensi [MIT](LICENSE). Bebas digunakan untuk keperluan komersial, pelatihan korporat, maupun institusi pendidikan.
