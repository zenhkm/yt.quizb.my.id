# 🚀 Quick Start Guide

## Untuk Development (Lokal)

### 1. Clone Repository
```bash
cd C:\Users\zenhk\OneDrive\Documents\GitHub
git clone https://github.com/yourusername/yt.quizb.my.id.git
cd yt.quizb.my.id
```

### 2. Setup Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# atau
source .venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Update yt-dlp (Penting!)
```bash
python update_ytdlp.py
```

### 5. Run Application
```bash
python app.py
```

### 6. Open Browser
```
http://localhost:5000
```

## ⚠️ Jika Masih Error 403

### Solusi 1: Update yt-dlp
```bash
python update_ytdlp.py
# Restart app setelah update
```

### Solusi 2: Manual Update
```bash
pip install --upgrade yt-dlp
```

### Solusi 3: Check Version
```bash
python -c "import yt_dlp; print(yt_dlp.version.__version__)"
# Harus: 2024.12.13 atau lebih baru
```

### Solusi 4: Restart App
```bash
# Ctrl+C untuk stop
python app.py  # Run lagi
```

## 🌐 Untuk Production (cPanel/Hosting)

### 1. Upload Files
Upload semua file via FTP/SFTP ke folder web root:
- app.py
- passenger_wsgi.py
- requirements.txt
- templates/
- tmp/

### 2. Setup Python (cPanel)
1. Buka **Python Selector** di cPanel
2. Create New Application:
   - Python Version: 3.8 atau lebih tinggi
   - Application Root: `/home/username/public_html`
   - Application URL: Domain Anda
   - Application Startup File: `passenger_wsgi.py`

### 3. Install Dependencies
Di terminal cPanel:
```bash
cd /home/username/public_html
source /home/username/virtualenv/public_html/3.8/bin/activate
pip install -r requirements.txt
```

### 4. Update yt-dlp
```bash
pip install --upgrade yt-dlp
```

### 5. Restart Application
```bash
touch tmp/restart.txt
```

### 6. Test
Buka domain Anda di browser.

## 📝 Maintenance

### Update yt-dlp (Rutin Seminggu Sekali)
```bash
# Development
python update_ytdlp.py

# Production (cPanel)
pip install --upgrade yt-dlp
touch tmp/restart.txt
```

### Check ffmpeg
```bash
# Development
ffmpeg -version

# Production
which ffmpeg
# atau cek via API: http://domain.com/api/check-ffmpeg
```

## 🐛 Troubleshooting

### Error: Module not found
```bash
pip install -r requirements.txt
```

### Error: ffmpeg not found
Install ffmpeg:
- **Windows**: Download dari https://ffmpeg.org
- **Linux**: `sudo apt install ffmpeg`
- **cPanel**: Contact hosting provider

### Error: 403 Forbidden
1. Update yt-dlp: `pip install -U yt-dlp`
2. Restart app
3. Tunggu 5-10 menit (rate limit)
4. Coba video lain

### Error: Port already in use
```bash
# Kill process di port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux:
lsof -ti:5000 | xargs kill -9
```

## ✅ Verification

Test dengan video YouTube apapun:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Jika berhasil download = SUKSES! 🎉

## 💡 Tips

1. **Update yt-dlp rutin** - YouTube sering update
2. **Jangan spam download** - Bisa kena rate limit
3. **Gunakan video public** - Private/age-restricted bisa gagal
4. **Check ffmpeg** - Pastikan tersedia di server
5. **Monitor logs** - Lihat terminal untuk debug

## 📚 More Help

- README.md - Full documentation
- CHANGELOG.md - Version history
- deploy.sh - Deployment script
