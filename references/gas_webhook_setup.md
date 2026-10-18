# Panduan Integrasi Google Apps Script (GAS) Webhook & Google Sheets

Panduan lengkap untuk menyiapkan endpoint serverless Google Apps Script yang menerima data hasil kuis e-learning secara real-time dan menyimpan/meng-update skor peserta di Google Sheets.

---

## 1. Persiapan Google Spreadsheet
1. Buka [Google Sheets](https://sheets.new) dan buat Spreadsheet baru.
2. Beri nama file (contoh: `Database_Nilai_Pelatihan_2026`).
3. Pada **Sheet1** (atau sheet aktif pertama), buat header di baris ke-1 sebagai berikut:

| Kolom A | Kolom B | Kolom C | Kolom D | Kolom E | Kolom F | Kolom G | Kolom H |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Timestamp** | **Nama** | **NIP** | **Jabatan** | **Divisi** | **Skor** | **Status** | **Attempt** |

---

## 2. Pemasangan Google Apps Script
1. Di Google Sheets, buka menu **Extensions (Ekstensi)** > **Apps Script**.
2. Hapus seluruh isi default pada `Code.gs`, lalu tempelkan (paste) kode berikut:

```javascript
function doPost(e) {
  var lock = LockService.getScriptLock();
  // Kunci script selama maks 10 detik untuk mencegah race-condition saat 50+ peserta submit bersamaan
  lock.tryLock(10000);
  
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);
    
    var newNip = String(data.nip || "").trim();
    var newScore = Number(data.skor) || 0;
    
    if (!newNip) {
      return ContentService.createTextOutput(JSON.stringify({
        result: "error", 
        message: "NIP wajib diisi"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    var lastRow = sheet.getLastRow();
    var foundRowIndex = -1;
    var existingScore = -1;
    
    // Baris 1 adalah header, data dimulai dari baris 2
    if (lastRow > 1) {
      var nipRange = sheet.getRange(2, 3, lastRow - 1, 1).getValues(); // Kolom C (NIP)
      var scoreRange = sheet.getRange(2, 6, lastRow - 1, 1).getValues(); // Kolom F (Skor)
      
      for (var i = 0; i < nipRange.length; i++) {
        if (String(nipRange[i][0]).trim() === newNip) {
          foundRowIndex = i + 2;
          existingScore = Number(scoreRange[i][0]) || 0;
          break;
        }
      }
    }
    
    if (foundRowIndex > -1) {
      // Mekanisme UPSERT: HANYA TIMPA jika nilai baru LEBIH TINGGI
      if (newScore > existingScore) {
        sheet.getRange(foundRowIndex, 1).setValue(new Date());
        sheet.getRange(foundRowIndex, 2).setValue(data.nama);
        sheet.getRange(foundRowIndex, 4).setValue(data.jabatan);
        sheet.getRange(foundRowIndex, 5).setValue(data.divisi);
        sheet.getRange(foundRowIndex, 6).setValue(newScore);
        sheet.getRange(foundRowIndex, 7).setValue(data.status);
        if (data.attempt) sheet.getRange(foundRowIndex, 8).setValue(data.attempt);
        
        return ContentService.createTextOutput(JSON.stringify({
          result: "updated", 
          message: "Data lama berhasil diperbarui dengan nilai yang lebih tinggi"
        })).setMimeType(ContentService.MimeType.JSON);
      } else {
        return ContentService.createTextOutput(JSON.stringify({
          result: "skipped", 
          message: "Nilai lama lebih tinggi atau sama, data tidak ditimpa"
        })).setMimeType(ContentService.MimeType.JSON);
      }
    } else {
      // NIP belum pernah ada, buat baris baru
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
      return ContentService.createTextOutput(JSON.stringify({
        result: "created", 
        message: "Data baru berhasil ditambahkan"
      })).setMimeType(ContentService.MimeType.JSON);
    }
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      result: "error", 
      error: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}
```

---

## 3. Deployment sebagai Web App
1. Klik tombol **Deploy (Terapkan)** di pojok kanan atas > **New deployment (Penerapan baru)**.
2. Klik ikon gerigi (Select type) > pilih **Web app**.
3. Atur konfigurasi deployment:
   - **Description**: `E-Learning Quiz Receiver v1`
   - **Execute as**: `Me (email anda)`
   - **Who has access**: `Anyone (Siapa saja)` *(Wajib agar modul frontend dapat mengirim tanpa token OAuth login Google)*.
4. Klik **Deploy**.
5. Berikan izin akses (Authorize Access) akun Google Anda jika diminta.
6. Salin **Web App URL** yang berformat:
   `https://script.google.com/macros/s/AKfycb.../exec`

---

## 4. Konfigurasi di Modul E-Learning
Masukkan URL Web App tersebut ke blok `course` pada `content.json` (berlaku untuk seluruh modul), atau ke field `webhookUrl` pada slide `quiz` tertentu (lebih diprioritaskan):

```javascript
// Blok course di content.json — berlaku untuk semua slide kuis
{
  "course": {
    // ...
    "webhookUrl": "https://script.google.com/macros/s/AKfycb.../exec",
    "maxQuizAttempts": 5,
    "passingScore": 80,
    "enableGatingTimer": true,
    "gatingSeconds": 10
  }
}
```

```javascript
// Slide quiz tertentu — override untuk slide ini saja
{ "type": "quiz", "webhookUrl": "https://script.google.com/macros/s/AKfycb.../exec", "questions": [ /* ... */ ] }
```

Sistem frontend e-learning akan otomatis mengirimkan payload JSON via `fetch(webhookUrl, {method: 'POST', ...})` ketika kuis **lulus** (skor $\ge$ `passingScore`) **atau** ketika percobaan gagal **terakhir** sudah terpakai (attempt mencapai `maxQuizAttempts`). Condition engine: `state.quizPassed || state.quizAttemptCount >= maxQuizAttempts`. Percobaan gagal sebelum limit **tidak dikirim** untuk mencegah polusi data; attempt terakhir yang gagal tetap dikirim dengan `status` `"TIDAK LULUS (MAX ATTEMPT)"`.

Data yang dikirim: `nama`, `nip`, `jabatan`, `divisi`, `skor`, `status`, dan `attempt` — diambil dari kartu identitas peserta di halaman kuis (`jabatan`/`divisi` default `-` bila kosong). Seluruh state ini disimpan **di memori saja** (tidak ada `localStorage`/`sessionStorage`); refresh halaman akan mengosongkannya. Catatan: pada slide kuis dengan `askParticipantInfo: false`, `nama`/`nip` kosong sehingga endpoint menolak baris tersebut (`"NIP wajib diisi"`).
