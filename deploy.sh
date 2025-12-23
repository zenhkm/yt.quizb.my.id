#!/bin/bash
# Deploy script for shared hosting (cPanel)

echo "🚀 Deploying YouTube Downloader..."

# 1. Upload all files via FTP/SFTP atau file manager cPanel
echo "✅ Upload semua file ke server"

# 2. Create virtual environment (jika hosting support)
# Di cPanel: gunakan Python Selector
echo "📦 Setup Python environment via cPanel Python Selector"
echo "   - Python version: 3.8+"
echo "   - Application root: /home/username/public_html/ytdl"
echo "   - Application startup file: passenger_wsgi.py"

# 3. Install dependencies
echo "📥 Install dependencies via terminal atau Python Selector"
echo "   pip install -r requirements.txt"

# 4. Update yt-dlp regularly
echo "🔄 Update yt-dlp (penting!)"
echo "   pip install --upgrade yt-dlp"

# 5. Restart application
echo "🔃 Restart via cPanel atau:"
echo "   touch tmp/restart.txt"

echo ""
echo "✨ Deployment complete!"
echo "🌐 Access: http://yt.quizb.my.id"
echo ""
echo "⚠️  Troubleshooting 403:"
echo "   1. Update yt-dlp: pip install -U yt-dlp"
echo "   2. Touch restart.txt untuk restart app"
echo "   3. Check ffmpeg availability"
