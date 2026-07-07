# Raraa Data Management

## Konsep Gabungan
Proyek ini menggabungkan dua konsep utama:
1. `dataanalytics` — pipeline backend untuk upload, split, rekonsiliasi, dan laporan invoice.
2. `mind-map.html` — mockup UI dashboard modern yang menampilkan visualisasi proses, status, dan ringkasan keputusan.

Hasilnya adalah aplikasi Data Management terintegrasi yang fokus pada:
- query data invoice,
- rekonsiliasi GL vs Billing,
- visualisasi workflow,
- dan pelaporan profesional.

## Fungsi Utama yang Terintegrasi

### 1. Upload dan Validasi Data
- Unggah file Excel `.xlsx`/`.xls` dari pengguna.
- Simpan file mentah ke direktori `data/raw/`.
- Validasi format dan nama file.
- Beri umpan balik segera jika format tidak valid.

### 2. Split Sheet ke CSV
- Baca workbook Excel penuh dengan `pandas`.
- Ekspor setiap sheet ke file CSV di `data/split/`.
- Menyediakan struktur data terpisah untuk analisis lebih lanjut.

### 3. Rekonsiliasi dan Normalisasi
- Analisis data pivot dari file `pivot.csv`.
- Ekstrak sisi GL dan sisi Billing.
- Normalisasi nomor invoice dan nilai numeric.
- Hitung jumlah dan nilai selisih.
- Tentukan status:
  - `Match`
  - `Qty Discrepancy`
  - `Value Discrepancy`
  - `Qty & Value Discrepancy`
  - `Only in Bill`
  - `Only in GL`

### 4. Generate Report Otomatis
- Simpan hasil analisis ke `data/processed/result.csv` dan `data/processed/result.xlsx`.
- Hasilkan file HTML `ReconReport.html` dengan KPI, breakdown, dan top discrepancy.
- Dashboard statis dapat langsung diakses via route `/report`.

### 5. Visual Dashboard dan Mindmap Workflow
- Konsep frontend menampilkan:
  - header branding `Raraa Data Management`
  - ringkasan KPI
  - kontrol upload dan proses
  - langkah-langkah pipeline
  - chart status rekonsiliasi
  - top discrepancy table
  - mindmap proses dengan node status warna
- Desain mobile friendly yang responsif dan mudah dipahami pengguna finance.

### 6. Query dan Tracking
- Backend dapat menyediakan basis untuk query:
  - cari invoice berdasar nomor,
  - filter status rekonsiliasi,
  - lihat item yang hanya muncul di GL atau Billing.
- Frontend dapat menampilkan hasil query dalam tabel dan grafik.

### 7. Audit Trail dan Riwayat Proses
- Simpan hasil split dan laporan hasil rekonsiliasi.
- Catat alur proses sehingga setiap upload/reconcile dapat ditelusuri.
- Buat fitur riwayat upload dan hasil run di UI.

### 8. Integrasi Ekosistem Data Management
- Arsitektur menggabungkan:
  - Flask backend untuk API dan proses data.
  - Pandas / NumPy untuk transformasi dan analisis.
  - HTML/CSS/JS untuk dashboard modern dan interface.
- Potensi pengembangan selanjutnya:
  - Google Sheets lookup/PIC assignment,
  - notifikasi email/Slack,
  - koneksi SAP query,
  - AI-assisted summary dan follow-up.

## Bagaimana Kedua Konsep Saling Melengkapi

| Kebutuhan | `dataanalytics` | `mind-map.html` | Nilai Gabungan |
|---|---|---|---|
| Proses data invoice | ✔ | ❌ | Backend lengkap untuk upload, split, reconcile |
| Laporan hasil | ✔ | ❌ | Otomatis HTML/CSV/XLSX report generation |
| Visualisasi workflow | ❌ | ✔ | UI mockup untuk dashboard dan mindmap |
| Mobile-friendly | ❌ | ✔ | Tampilan responsif dengan styling modern |
| Query / filter | Dasar | Desain UX | Potensi query integrasi dengan UI |
| Audit / riwayat | Dasar | Desain proses | Jejak data dan status pemrosesan |

## Ide Fitur Terintegrasi

### A. Dashboard Data Management
- Panel upload Excel dengan validasi penuh.
- Ringkasan status rekonsiliasi (match, discrepancy, missing).
- Process flow visual dengan node upload → split → reconcile → report.
- Log aktivitas realtime.

### B. Report dan Export Otomatis
- Ekspor hasil rekonsiliasi ke CSV, XLSX, HTML.
- Template laporan yang bisa dipersonalisasi.
- Summary KPI, breakdown status, top 5 discrepancy.

### C. Query dan Filter Invoice
- Cari invoice berdasarkan nomor, status, atau nilai selisih.
- Filter data GL-only, Billing-only, mismatch.
- Tampilkan hasil query di tabel interaktif.

### D. PIC Assignment dan Follow-up
- Integrasi matrix PIC berdasarkan tahun atau unit bisnis.
- Tautkan setiap discrepancy ke penanggung jawab.
- Siapkan pesan follow-up untuk email/Slack.

### E. Audit dan History
- Tampilkan rangkuman upload terakhir, status proses, dan nama file.
- Simpan snapshot hasil proses untuk review dan compliance.

### F. Integrasi Eksternal Masa Depan
- Google Sheets API untuk lookup data tambahan.
- Gmail / Slack webhook untuk notifikasi.
- SAP Query untuk validasi status GI/Clearing.
- OpenAI untuk ringkasan laporan profesional.

## Rekomendasi Struktur README
1. Deskripsi singkat aplikasi.
2. Fitur utama.
3. Arsitektur singkat.
4. Alur penggunaan.
5. Direktori penting.
6. Pengembangan selanjutnya.

## Rekap Fungsi yang Bisa Diatasi oleh Kedua Konsep
- Menyediakan platform data management yang fokus pada invoice reconciliation.
- Menyatukan proses ekstraksi data, analisis selisih, dan pelaporan.
- Memberikan UI yang mudah dimengerti untuk pengguna non-teknis.
- Menyiapkan pondasi untuk query, audit, dan notifikasi.
- Menjadikan aplikasi siap berkembang menjadi sistem end-to-end.

---

## Kesimpulan
Kedua konsep dapat digabungkan menjadi satu solusi data management yang lengkap:
- backend `dataanalytics` sebagai engine pemrosesan,
- frontend `mind-map.html` sebagai pengalaman pengguna visual,
- dan `readme.md` ini sebagai panduan fitur dan tujuan integrasi.

Aplikasi hasil integrasi akan menjadi sistem reconcilation & query yang profesional, cepat dipahami, dan siap dikembangkan lebih lanjut.