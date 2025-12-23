from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp
import requests  # Import library baru ini
import re

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_video_info():
    data = request.get_json(silent=True) or {}
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL tidak boleh kosong'}), 400

    ydl_opts = {
        # Windows-friendly: prefer H.264 (avc1) + AAC (mp4a) in MP4 container.
        # If unavailable, fall back to any MP4 with audio+video, then best.
        'format': (
            'best[ext=mp4][vcodec^=avc1][acodec^=mp4a][acodec!=none][vcodec!=none]'
            '/best[ext=mp4][vcodec^=avc1][acodec!=none][vcodec!=none]'
            '/best[ext=mp4][acodec!=none][vcodec!=none]'
            '/best'
        ),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
        },
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_data = {
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string') or info.get('duration'),
                'url': info.get('url'), # Ini URL asli dari Google
                'ext': info.get('ext')
            }
            return jsonify(video_data)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json(silent=True) or {}
    url = data.get('url')

    if not url:
        return "URL tidak boleh kosong", 400

    ydl_opts = {
        # Windows-friendly: prefer H.264 (avc1) + AAC (mp4a) in MP4 container.
        # If unavailable, fall back to any MP4 with audio+video, then best.
        'format': (
            'best[ext=mp4][vcodec^=avc1][acodec^=mp4a][acodec!=none][vcodec!=none]'
            '/best[ext=mp4][vcodec^=avc1][acodec!=none][vcodec!=none]'
            '/best[ext=mp4][acodec!=none][vcodec!=none]'
            '/best'
        ),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        file_url = info.get('url')
        if not file_url:
            return "Gagal mendapatkan direct URL", 500

        title = _safe_filename(info.get('title') or 'video')
        ext = (info.get('ext') or 'mp4').strip('.')
        vcodec = (info.get('vcodec') or '').strip()
        acodec = (info.get('acodec') or '').strip()
        format_id = (info.get('format_id') or '').strip()

        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept-Encoding': 'identity',
        }
        req = requests.get(file_url, stream=True, headers=headers, timeout=30)
        req.raise_for_status()

        content_type = req.headers.get('content-type') or 'application/octet-stream'
        content_length = req.headers.get('content-length')

        # Peek first chunk to avoid saving HTML/playlist as .mp4
        content_iter = req.iter_content(chunk_size=1024 * 256)
        first_chunk = next(content_iter, b'')
        if not first_chunk:
            return "Upstream mengembalikan data kosong", 502

        sniff = first_chunk[:64].lstrip()
        if sniff.startswith(b'<!doctype') or sniff.startswith(b'<!DOCTYPE') or sniff.startswith(b'<html'):
            return "Upstream mengembalikan HTML (bukan file video)", 502

        # MP4 typically contains 'ftyp' early; WebM starts with EBML header.
        if ext.lower() == 'mp4' and b'ftyp' not in first_chunk[:4096]:
            if first_chunk.startswith(b'\x1a\x45\xdf\xa3'):
                ext = 'webm'
                content_type = 'video/webm'

        response_headers = {
            'Content-Disposition': f'attachment; filename="{title}.{ext}"',
            'X-File-Ext': ext,
            'X-VCodec': vcodec,
            'X-ACodec': acodec,
            'X-Format-Id': format_id,
        }
        if content_length:
            response_headers['Content-Length'] = content_length

        def generate():
            yield first_chunk
            for chunk in content_iter:
                if chunk:
                    yield chunk

        return Response(
            stream_with_context(generate()),
            content_type=content_type,
            headers=response_headers,
        )
    except Exception as e:
        return f"Error: {e}", 500

# --- TAMBAHKAN BAGIAN INI ---
@app.route('/download_proxy')
def download_proxy():
    file_url = request.args.get('url')
    title = request.args.get('title', 'video')
    ext = request.args.get('ext', 'mp4')
    
    if not file_url:
        return "URL tidak ditemukan", 400

    title = _safe_filename(title or 'video')
    ext = (ext or 'mp4').strip('.')

    headers = {
        'User-Agent': 'Mozilla/5.0',
    }

    # Server mendownload file dari Google secara streaming
    req = requests.get(file_url, stream=True, headers=headers, timeout=30)
    req.raise_for_status()

    # Server meneruskan (pipe) data langsung ke user
    return Response(
        stream_with_context(req.iter_content(chunk_size=1024)),
        content_type=req.headers.get('content-type') or 'application/octet-stream',
        headers={
            'Content-Disposition': f'attachment; filename="{title}.{ext}"'
        }
    )
# ----------------------------

if __name__ == '__main__':
    app.run(debug=True, port=5000)