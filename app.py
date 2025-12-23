from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_file, after_this_request
from flask_cors import CORS
import yt_dlp
import requests  # Import library baru ini
import re
import os
import shutil
import tempfile
from typing import Optional, Dict, Any

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


def _pick_direct_mp4_format(info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    formats = info.get('formats') or []
    candidates: list[Dict[str, Any]] = []

    for f in formats:
        url = f.get('url')
        if not url:
            continue

        ext = (f.get('ext') or '').lower()
        if ext != 'mp4':
            continue

        acodec = (f.get('acodec') or '').lower()
        vcodec = (f.get('vcodec') or '').lower()
        if acodec in ('', 'none') or vcodec in ('', 'none'):
            continue

        protocol = (f.get('protocol') or '').lower()
        # Avoid manifest-based streams (HLS/DASH) when proxying
        if 'm3u8' in protocol or 'dash' in protocol:
            continue
        if not (protocol.startswith('http') or url.startswith('http')):
            continue
        if 'm3u8' in url.lower():
            continue

        candidates.append(f)

    if not candidates:
        return None

    def score(f: Dict[str, Any]) -> tuple:
        vcodec = (f.get('vcodec') or '').lower()
        acodec = (f.get('acodec') or '').lower()
        prefer_avc = 1 if vcodec.startswith('avc1') else 0
        prefer_aac = 1 if acodec.startswith('mp4a') else 0
        height = f.get('height') or 0
        tbr = f.get('tbr') or 0
        return (prefer_avc, prefer_aac, height, tbr)

    return sorted(candidates, key=score, reverse=True)[0]


def _has_usable_ffmpeg() -> Optional[str]:
    env_path = os.environ.get('FFMPEG_LOCATION')
    if env_path and os.path.exists(env_path):
        return env_path

    # Common path in your hosting setup (safe if missing)
    hosting_path = '/home/quic1934/ffmpeg/ffmpeg-7.0.2-amd64-static'
    if os.path.exists(hosting_path):
        return hosting_path

    return shutil.which('ffmpeg')


def _download_with_ytdlp(source_url: str, tmpdir: str, ffmpeg_path: Optional[str]) -> str:
    outtmpl = os.path.join(tmpdir, '%(title).150s.%(ext)s')
    dl_opts: Dict[str, Any] = {
        'format': (
            'best[ext=mp4][vcodec^=avc1][acodec^=mp4a][acodec!=none][vcodec!=none]'
            '/best[ext=mp4][acodec!=none][vcodec!=none]'
            '/best'
        ),
        'outtmpl': outtmpl,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
        },
    }
    if ffmpeg_path:
        dl_opts['ffmpeg_location'] = ffmpeg_path

    with yt_dlp.YoutubeDL(dl_opts) as ydl:
        downloaded_info = ydl.extract_info(source_url, download=True)
        file_path = ydl.prepare_filename(downloaded_info)

    if not os.path.exists(file_path):
        base, _ = os.path.splitext(file_path)
        mp4_path = base + '.mp4'
        if os.path.exists(mp4_path):
            file_path = mp4_path

    return file_path

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

        title = _safe_filename(info.get('title') or 'video')

        picked = _pick_direct_mp4_format(info)
        if picked:
            file_url = picked.get('url')
            ext = 'mp4'
            vcodec = (picked.get('vcodec') or '').strip()
            acodec = (picked.get('acodec') or '').strip()
            format_id = (picked.get('format_id') or '').strip()
        else:
            file_url = info.get('url')
            ext = (info.get('ext') or 'mp4').strip('.')
            vcodec = (info.get('vcodec') or '').strip()
            acodec = (info.get('acodec') or '').strip()
            format_id = (info.get('format_id') or '').strip()

        if not file_url:
            return "Gagal mendapatkan URL stream", 500

        # Use headers that yt-dlp expects for the chosen format (helps avoid 403)
        format_headers = {}
        if picked and isinstance(picked, dict):
            format_headers = picked.get('http_headers') or {}
        if not format_headers:
            format_headers = info.get('http_headers') or {}

        headers = {
            **format_headers,
            'User-Agent': format_headers.get('User-Agent') or 'Mozilla/5.0',
            'Referer': format_headers.get('Referer') or 'https://www.youtube.com/',
            'Origin': format_headers.get('Origin') or 'https://www.youtube.com',
            'Accept-Encoding': 'identity',
        }

        try:
            req = requests.get(file_url, stream=True, headers=headers, timeout=30)
            req.raise_for_status()
        except requests.HTTPError as http_err:
            status = getattr(http_err.response, 'status_code', None)
            if status in (401, 403):
                # Fallback: let yt-dlp do the download (handles YouTube quirks better)
                tmpdir = tempfile.mkdtemp(prefix='ytdlp_')

                @after_this_request
                def _cleanup(response):
                    shutil.rmtree(tmpdir, ignore_errors=True)
                    return response

                ffmpeg_path = _has_usable_ffmpeg()
                file_path = _download_with_ytdlp(url, tmpdir, ffmpeg_path)
                if not os.path.exists(file_path):
                    return f"Error: fallback download gagal (HTTP {status})", 502

                download_name = os.path.basename(file_path)
                guessed_mime = 'video/mp4' if download_name.lower().endswith('.mp4') else 'application/octet-stream'
                return send_file(file_path, as_attachment=True, download_name=download_name, mimetype=guessed_mime)
            raise

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

        if sniff.startswith(b'#EXTM3U'):
            # This is an HLS manifest, not a media file.
            # If no direct MP4 exists, we need yt-dlp download+merge.
            picked = None

        # MP4 typically contains 'ftyp' early; WebM starts with EBML header.
        if ext.lower() == 'mp4' and b'ftyp' not in first_chunk[:4096]:
            if first_chunk.startswith(b'\x1a\x45\xdf\xa3'):
                ext = 'webm'
                content_type = 'video/webm'
            elif sniff.startswith(b'#EXTM3U'):
                # Force fallback path below
                picked = None

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

        # If we detected HLS manifest, use fallback downloader if possible.
        if sniff.startswith(b'#EXTM3U'):
            ffmpeg_path = _has_usable_ffmpeg()
            if not ffmpeg_path:
                return "Sumber video hanya menyediakan stream HLS (m3u8). Server butuh ffmpeg untuk menggabungkan jadi MP4.", 502

            tmpdir = tempfile.mkdtemp(prefix='ytdlp_')

            @after_this_request
            def _cleanup(response):
                shutil.rmtree(tmpdir, ignore_errors=True)
                return response

            file_path = _download_with_ytdlp(url, tmpdir, ffmpeg_path)
            if not os.path.exists(file_path):
                return "Gagal membuat file hasil download di server", 500

            download_name = os.path.basename(file_path)
            guessed_mime = 'video/mp4' if download_name.lower().endswith('.mp4') else 'application/octet-stream'
            return send_file(file_path, as_attachment=True, download_name=download_name, mimetype=guessed_mime)

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