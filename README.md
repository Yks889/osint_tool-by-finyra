# OSINT Social Media Finder

**Versi:** v1.0 (2025)
**Dibuat oleh:** [Finyra Software Design Studio](https://github.com/finyra)

## 📌 Deskripsi

OSINT Social Media Finder adalah alat **Open Source Intelligence (OSINT)** untuk menemukan profil media sosial berdasarkan **email** atau **username**.
Fitur utama:
✅ Pencarian otomatis di berbagai platform sosial media
✅ Dukungan fallback (Google / DuckDuckGo) jika permintaan diblokir
✅ Scraping data profil (nama, bio, lokasi, email, nomor telepon)
✅ Ekstraksi kontak dari halaman profil
✅ Mode **Instagram OSINT** dengan login session untuk data lebih detail
✅ Output dalam format **JSON**, **CSV**, dan **HTML Report**

---
## Gui Tampilan 

  /$$$$$$   /$$$$$$  /$$$$$$ /$$   /$$ /$$$$$$$$       /$$    /$$   /$$  
 /$$__  $$ /$$__  $$|_  $$_/| $$$ | $$|__  $$__/      | $$   | $$ /$$$$  
| $$  \ $$| $$  \__/  | $$  | $$$$| $$   | $$         | $$   | $$|_  $$  
| $$  | $$|  $$$$$$   | $$  | $$ $$ $$   | $$         |  $$ / $$/  | $$  
| $$  | $$ \____  $$  | $$  | $$  $$$$   | $$          \  $$ $$/   | $$  
| $$  | $$ /$$  \ $$  | $$  | $$\  $$$   | $$           \  $$$/    | $$  
|  $$$$$$/|  $$$$$$/ /$$$$$$| $$ \  $$   | $$            \  $/    /$$$$$$
 \______/  \______/ |______/|__/  \__/   |__/             \_/    |______/

================================================================================
  OSINT Social Media Finder v1 2025
  Powered by Finyra Software Design Studio
================================================================================

[1] 🔍 Scan Social Media by Email
[2] 🔎 Scan Social Media by Username
[3] ⚙️ Change Output Format (JSON/CSV)
[4] 📸 OSINT Instagram (username only)
[5] ❌ Exit
--------------------------------------------------
[?] Pilih opsi:

---

## ⚙️ Fitur Utama

* **Multi-threaded scanning** (cepat & efisien)
* **Instagram Advanced Mode** (menggunakan Instaloader session)
* **Deteksi lokasi & kontak**
* **Export hasil ke JSON, CSV, dan HTML report**
* **Fallback Search** jika permintaan diblokir (Captcha / HTTP 429)

---

## 🖥️ Cara Install

Pastikan Python 3.8+ sudah terpasang.
Clone repository ini:

```bash
git clone https://github.com/username/osint-social-finder.git
cd osint-social-finder
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### **Requirements:**

* `requests`
* `beautifulsoup4`
* `instaloader`

Jika belum ada file `requirements.txt`, buat dengan isi berikut:

```
requests
beautifulsoup4
instaloader
```

---

## ▶️ Cara Menggunakan

Jalankan script:

```bash
python3 osint_finder.py
```

Menu utama:

```
[1] 🔍 Scan Social Media by Email
[2] 🔎 Scan Social Media by Username
[3] ⚙️ Change Output Format (JSON/CSV)
[4] 📸 OSINT Instagram (username only)
[5] ❌ Exit
```

### **Contoh Penggunaan**

1. **Scan berdasarkan email:**

   ```
   Pilih opsi: 1
   Masukkan Email: example@gmail.com
   Jumlah threads [6]: 6
   ```

   Hasil akan disimpan ke folder **output/**.

2. **Scan berdasarkan username:**

   ```
   Pilih opsi: 2
   Masukkan Username: johndoe
   ```

3. **Instagram OSINT (Advanced):**

   ```
   Pilih opsi: 4
   Masukkan username IG session: akun_login
   Masukkan path session file: /home/user/.config/instaloader/session-akun_login
   Masukkan Instagram Username target: target_user
   ```

---

## 📂 Output

Hasil scan akan tersimpan di folder **output/** dalam format:

* `JSON` → untuk pemrosesan data
* `CSV` → untuk spreadsheet
* `HTML` → untuk laporan yang rapi

Contoh nama file:

```
results_username_1735373812.json
results_email_1735373812.csv
instagram_target_1735373812.html
```

---

## 🔒 Catatan Penting

* Gunakan secara etis dan sesuai hukum yang berlaku.
* Jangan gunakan untuk kejahatan siber atau pelanggaran privasi.
* Aplikasi ini hanya untuk **OSINT & Penetration Testing dengan izin**.

---

## 🛠️ To-Do (Pengembangan)

* [ ] Mode CLI → Mode Web Dashboard
* [ ] Dukungan Proxy & Rotasi User-Agent lebih kompleks
* [ ] Integrasi database hasil scan
* [ ] Multi-target input (batch scan)

---

## 👨‍💻 Kontributor

Dibuat oleh **Finyra Software Design Studio**.
Jika ingin berkontribusi, silakan fork repository ini dan buat **Pull Request**.

---

## 📜 Lisensi

Proyek ini dirilis di bawah lisensi **MIT**.
Silakan digunakan, diubah, dan didistribusikan dengan mencantumkan kredit.
