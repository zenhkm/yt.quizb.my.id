# 🎮 Command Reference

## Quick Commands

### Development

#### Start App
```bash
# Windows
.venv\Scripts\activate
python app.py

# Linux/Mac
source .venv/bin/activate
python app.py
```

#### Update yt-dlp
```bash
python update_ytdlp.py
```

#### Install/Update Dependencies
```bash
pip install -r requirements.txt
```

#### Check Versions
```bash
# yt-dlp version
python -c "import yt_dlp; print(yt_dlp.version.__version__)"

# Flask version
python -c "import flask; print(flask.__version__)"

# Python version
python --version
```

### Production (cPanel)

#### Restart App
```bash
touch tmp/restart.txt
```

#### Update yt-dlp
```bash
source /home/username/virtualenv/public_html/3.8/bin/activate
pip install --upgrade yt-dlp
touch tmp/restart.txt
```

#### View Logs
```bash
tail -f stderr.log
```

#### Check ffmpeg
```bash
which ffmpeg
ffmpeg -version
```

### Git Commands

#### Commit Changes
```bash
git add .
git commit -m "Fix: Enhanced 403 bypass system"
git push origin main
```

#### Pull Updates
```bash
git pull origin main
```

#### Check Status
```bash
git status
git log --oneline -10
```

### Troubleshooting

#### Kill Process on Port 5000
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux
lsof -ti:5000 | xargs kill -9
```

#### Reinstall All Dependencies
```bash
pip uninstall -y -r requirements.txt
pip install -r requirements.txt
```

#### Clear Cache
```bash
# Windows
rmdir /s /q __pycache__
rmdir /s /q .venv

# Linux
rm -rf __pycache__ .venv
```

#### Test yt-dlp Directly
```bash
# Check if yt-dlp works
yt-dlp --version

# Download a video
yt-dlp "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Get video info only
yt-dlp --get-title --get-duration "URL"
```

### API Testing

#### Using curl
```bash
# Check ffmpeg
curl http://localhost:5000/api/check-ffmpeg

# Get video info
curl -X POST http://localhost:5000/api/info \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Download (saves to current directory)
curl -X POST http://localhost:5000/api/download \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  --output video.mp4
```

#### Using PowerShell
```powershell
# Check ffmpeg
Invoke-RestMethod -Uri "http://localhost:5000/api/check-ffmpeg"

# Get video info
$body = @{url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:5000/api/info" `
  -ContentType "application/json" -Body $body
```

### Environment Setup

#### Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

#### Deactivate Virtual Environment
```bash
deactivate
```

### Performance Monitoring

#### Check Memory Usage
```bash
# Windows
tasklist | findstr python

# Linux
ps aux | grep python
```

#### Check Disk Space
```bash
# Windows
dir tmp /s

# Linux
du -sh tmp/
```

### Backup & Restore

#### Backup
```bash
# Create backup
tar -czf yt-downloader-backup-$(date +%Y%m%d).tar.gz \
  app.py templates/ requirements.txt passenger_wsgi.py

# Or zip
zip -r backup.zip . -x ".venv/*" "__pycache__/*" "*.pyc"
```

#### Restore
```bash
# Extract backup
tar -xzf yt-downloader-backup-20241223.tar.gz

# Install dependencies
pip install -r requirements.txt
```

### Database/Cache Management

#### Clear Temporary Files
```bash
# Windows
del /q tmp\*.*

# Linux
rm -f tmp/*
```

### Security

#### Update All Packages
```bash
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```

#### Check for Vulnerabilities
```bash
pip check
pip list --outdated
```

## One-Liners

### Quick Setup
```bash
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && python update_ytdlp.py && python app.py
```

### Quick Update
```bash
pip install --upgrade yt-dlp && python app.py
```

### Quick Test
```bash
curl -X POST http://localhost:5000/api/info -H "Content-Type: application/json" -d "{\"url\":\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}"
```

### Production Deploy
```bash
git pull && pip install -r requirements.txt && pip install --upgrade yt-dlp && touch tmp/restart.txt
```

## Maintenance Schedule

### Daily
- Check logs: `tail -f stderr.log`

### Weekly
- Update yt-dlp: `python update_ytdlp.py`
- Check disk space
- Review error logs

### Monthly
- Update all dependencies: `pip install --upgrade -r requirements.txt`
- Security check: `pip check`
- Backup files

## Emergency Commands

### App Not Responding
```bash
# Kill and restart
Ctrl+C
python app.py
```

### 403 Errors
```bash
python update_ytdlp.py
# Restart app
```

### Out of Disk Space
```bash
# Clear temp files
rm -rf tmp/*
# Clear old logs
> stderr.log
```

### ffmpeg Missing
```bash
# Windows: Download and install from ffmpeg.org
# Linux:
sudo apt update && sudo apt install ffmpeg
```

---

## 💡 Pro Tips

1. **Always use virtual environment** to avoid conflicts
2. **Update yt-dlp weekly** - YouTube changes frequently
3. **Monitor stderr.log** for hidden errors
4. **Keep backups** before major updates
5. **Test locally** before deploying to production
6. **Use touch tmp/restart.txt** for graceful restart on cPanel
7. **Check API responses** with curl/Postman for debugging
8. **Keep Python updated** but test before upgrading

## 📞 Need Help?

Run these diagnostic commands and share output:
```bash
python --version
python -c "import yt_dlp; print(yt_dlp.version.__version__)"
pip list | grep -E "(flask|yt-dlp|requests)"
which ffmpeg
curl http://localhost:5000/api/check-ffmpeg
```
