from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_file
from flask_cors import CORS
import yt_dlp
import requests
import re
import os
import shutil

app = Flask(__name__)
CORS(app)


def _safe_filename(name: str, fallback: str = "video") -> str:
    if not name:
        name = fallback
    name = name.strip()
    name = re.sub(r"[\r\n\t]", " ", name)
    name = re.sub(r"[\\/:*?\"<>|]", "-", name)
    name = re.sub(r"\s+", " ", name)
    return name[:150] if len(name) > 150 else name


def _has_usable_ffmpeg() -> str:
    """Check if ffmpeg is available in the system."""
    # First check environment variable
    env_path = os.environ.get('FFMPEG_LOCATION')
    if env_path and os.path.exists(env_path):
        return env_path
    
    # Common path in your hosting setup
    hosting_path = '/home/quic1934/ffmpeg/ffmpeg-7.0.2-amd64-static'
    if os.path.exists(hosting_path):
        return hosting_path
    
    # System ffmpeg
    which_result = shutil.which('ffmpeg')
    return which_result if which_result else ""


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/check-ffmpeg', methods=['GET'])
def check_ffmpeg():
    """Check if ffmpeg is available on the server."""
    ffmpeg_path = _has_usable_ffmpeg()
    return jsonify({
        'ffmpeg_available': bool(ffmpeg_path),
        'ffmpeg_path': ffmpeg_path or 'Not found',
    })


@app.route('/api/info', methods=['POST'])
def get_video_info():
    """Get video info (title, thumbnail, duration) without downloading."""
    data = request.get_json(silent=True) or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'URL tidak boleh kosong'}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return jsonify({
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string') or str(info.get('duration', 0)),
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def api_download():
    """Download video: try direct MP4 proxy first, then fallback to yt-dlp if needed."""
    data = request.get_json(silent=True) or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'URL tidak boleh kosong'}), 400

    try:
        # Extract info to find best format
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        title = _safe_filename(info.get('title') or 'video')
        
        # Find a direct HTTP MP4 URL (avoid HLS/DASH manifests)
        file_url = None
        file_ext = 'mp4'
        
        formats = info.get('formats') or []
        for fmt in formats:
            fmt_url = fmt.get('url', '')
            fmt_ext = (fmt.get('ext') or '').lower()
            
            # Skip manifests and non-HTTP
            if 'm3u8' in fmt_url.lower() or 'dash' in (fmt.get('protocol') or '').lower():
                continue
            
            # Prefer MP4 with both audio and video
            if fmt_ext == 'mp4':
                if fmt.get('vcodec') not in (None, 'none') and fmt.get('acodec') not in (None, 'none'):
                    file_url = fmt_url
                    break
        
        # Fallback to best format if no suitable MP4 found
        if not file_url:
            file_url = info.get('url')
            file_ext = info.get('ext', 'mp4')
        
        if not file_url:
            return jsonify({'error': 'Tidak dapat menemukan URL video yang valid'}), 500

        # Try to proxy the direct URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.youtube.com/',
            'Origin': 'https://www.youtube.com',
        }
        
        try:
            # Use a shorter timeout to fail fast
            resp = requests.head(file_url, headers=headers, timeout=5, allow_redirects=True)
            if resp.status_code not in (200, 206):
                raise Exception(f'HTTP {resp.status_code}')
        except Exception as head_err:
            # If HEAD fails, just try GET (it might work anyway)
            pass
        
        # Stream the video
        try:
            req = requests.get(file_url, stream=True, headers=headers, timeout=30)
            req.raise_for_status()
        except requests.HTTPError as e:
            status = e.response.status_code if e.response else 0
            if status in (401, 403):
                return jsonify({
                    'error': f'Server video menolak akses (HTTP {status}). URL mungkin sudah expired.',
                    'suggestion': 'Gunakan yt-dlp lokal: yt-dlp -f best <url>'
                }), 502
            raise
        
        # Peek first chunk to ensure it's actually a video file
        def generate():
            chunks_sent = 0
            for chunk in req.iter_content(chunk_size=1024 * 256):
                if chunk:
                    # Check first chunk
                    if chunks_sent == 0:
                        first_64 = chunk[:64]
                        if first_64.startswith(b'<!doctype') or first_64.startswith(b'<html') or first_64.startswith(b'#EXTM3U'):
                            raise ValueError('Server returned HTML or HLS manifest, not a video file')
                    yield chunk
                    chunks_sent += 1
        
        return Response(
            generate(),
            content_type='video/mp4',
            headers={
                'Content-Disposition': f'attachment; filename="{title}.{file_ext}"',
            }
        )
    
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
