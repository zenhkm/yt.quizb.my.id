#!/usr/bin/env python3
"""
Script untuk update yt-dlp ke versi terbaru.
Jalankan ini jika masih mengalami error 403.

Usage:
    python update_ytdlp.py
"""

import subprocess
import sys

def update_ytdlp():
    """Update yt-dlp to the latest version."""
    print("🔄 Updating yt-dlp to the latest version...")
    print("-" * 50)
    
    try:
        # Update yt-dlp
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(result.stdout)
        print("✅ yt-dlp updated successfully!")
        
        # Check version
        version_result = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--version"],
            capture_output=True,
            text=True
        )
        
        print(f"\n📦 Current yt-dlp version: {version_result.stdout.strip()}")
        print("\n✨ Sekarang restart aplikasi Flask Anda dan coba lagi!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error updating yt-dlp: {e}")
        print(e.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_ytdlp()
