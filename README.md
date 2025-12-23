# 🎥 YouTube Downloader - Enhanced Version

YouTube video downloader dengan fitur anti-403 bypass dan quality selection.

## ✨ Fitur Utama

- **🎯 Quality Selection** - Pilih kualitas video sebelum download (NEW!)
- **Anti-403 Bypass** - Menggunakan multiple player clients (Android, Web)
- **Auto Retry** - Otomatis retry 3x dengan exponential backoff
- **Enhanced Headers** - User-agent dan headers yang lebih baik
- **Better Error Messages** - Pesan error yang lebih informatif
- **Filesize Preview** - Lihat ukuran file sebelum download

## 🎯 Cara Menggunakan

1. **Paste URL YouTube** ke input field
2. **Klik "Cek Video"** - Aplikasi akan fetch available qualities
3. **Pilih Kualitas** yang diinginkan:
   - Best Quality (Auto) - Kualitas terbaik otomatis
   - 1080p - Full HD
   - 720p - HD
   - 480p - Standard Definition
   - 360p - Mobile Quality
4. **Klik "Download"** - Video akan didownload

### Quality Selection
```
┌────────────────────────────────┐
│  Best Quality    1080p   720p  │
│   (Auto)        ~50MB   ~30MB  │
├────────────────────────────────┤
│   480p          360p           │
│  ~15MB         ~10MB           │
└────────────────────────────────┘
```

## 🚀 Instalasi

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Update yt-dlp (Penting!)

```bash
python update_ytdlp.py
```

Atau manual:
```bash
pip install --upgrade yt-dlp
```

### 3. Jalankan Aplikasi

```bash
python app.py
```

## 🔧 Troubleshooting Error 403

### Solusi 1: Update yt-dlp
YouTube sering update sistemnya, jadi yt-dlp perlu update rutin:

```bash
python update_ytdlp.py
```

### Solusi 2: Restart Aplikasi
Setelah update, restart aplikasi Flask:

```bash
# Ctrl+C untuk stop
python app.py
```

### Solusi 3: Gunakan yt-dlp Lokal
Jika tetap error, download langsung di komputer:

```bash
yt-dlp [URL_VIDEO]
```

## 🛡️ Fitur Anti-403

Aplikasi ini menggunakan beberapa teknik untuk menghindari 403:

1. **Multiple Player Clients**: Mencoba Android dan Web player
2. **Enhanced Headers**: User-agent Firefox terbaru
3. **Retry Logic**: 3x retry dengan delay bertahap
4. **Fragment Retries**: Retry untuk setiap fragment video
5. **Timeout Handling**: Socket timeout 30 detik

## 📝 API Endpoints

### GET /
Halaman utama aplikasi

### POST /api/info
Get info video tanpa download
```json
{
  "url": "https://youtube.com/watch?v=..."
}
```

### POST /api/formats (NEW!)
Get available video qualities
```json
{
  "url": "https://youtube.com/watch?v=..."
}
```

Response:
```json
{
  "formats": [
    {
      "quality": "1080p",
      "height": 1080,
      "filesize_mb": 50.0
    }
  ],
  "title": "Video Title"
}
```

### POST /api/download
Download video dengan kualitas tertentu
```json
{
  "url": "https://youtube.com/watch?v=...",
  "quality": "720p"  // optional, default: "best"
}
```

### GET /api/check-ffmpeg
Cek ketersediaan ffmpeg

## 🔄 Update Regular

Untuk hasil terbaik, update yt-dlp seminggu sekali:

```bash
python update_ytdlp.py
```

## 📦 Dependencies

- Flask >= 3.0.0
- flask-cors >= 4.0.0
- yt-dlp >= 2024.12.13 (latest)
- requests >= 2.31.0

## 🌐 Deploy

### Shared Hosting (cPanel)
1. Upload semua file
2. Pastikan `passenger_wsgi.py` ada
3. Install dependencies via Python Selector
4. Set aplikasi ke `app.py`

### VPS/Cloud
1. Clone repository
2. Install dependencies
3. Setup systemd service atau gunicorn
4. Configure nginx/apache reverse proxy

## ⚠️ Catatan Penting

- **403 Error**: YouTube bisa sewaktu-waktu block. Update yt-dlp adalah solusi utama.
- **ffmpeg Required**: Server harus punya ffmpeg untuk merge video+audio.
- **Rate Limiting**: Jangan spam download, bisa kena rate limit.
- **Legal**: Gunakan sesuai ToS YouTube dan hukum setempat.

## 🆘 Support

Jika masih error:
1. Update yt-dlp: `python update_ytdlp.py`
2. Restart aplikasi
3. Coba video lain (mungkin video specific issue)
4. Tunggu beberapa menit (rate limiting)
5. Gunakan yt-dlp lokal di komputer

## 📄 License

MIT License - Gunakan dengan bijak!
