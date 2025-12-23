from flask import Flask, render_template, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import yt_dlp
import requests
import re
import os
import shutil
import tempfile

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


def _get_ffmpeg() -> str:
    """Get ffmpeg path if available."""
    env_path = os.environ.get('FFMPEG_LOCATION')
    if env_path and os.path.exists(env_path):
        return env_path
    
    hosting_path = '/home/quic1934/ffmpeg/ffmpeg-7.0.2-amd64-static'
    if os.path.exists(hosting_path):
        return hosting_path
    
    which_result = shutil.which('ffmpeg')
    return which_result if which_result else ""


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/check-ffmpeg', methods=['GET'])
def check_ffmpeg():
    ffmpeg_path = _get_ffmpeg()
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
    """Download video using yt-dlp with ffmpeg merge."""
    data = request.get_json(silent=True) or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'URL tidak boleh kosong'}), 400

    ffmpeg_path = _get_ffmpeg()
    if not ffmpeg_path:
        return jsonify({'error': 'ffmpeg tidak tersedia di server. Gunakan yt-dlp lokal.'}), 503

    tmpdir = None
    try:
        # Create temp directory for download
        tmpdir = tempfile.mkdtemp(prefix='ytdlp_')

        # yt-dlp options: prefer H.264+AAC MP4
        ydl_opts = {
            'format': (
                'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a][acodec^=mp4a]'
                '/bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]'
                '/best[ext=mp4][vcodec^=avc1][acodec!=none][vcodec!=none]'
                '/best[ext=mp4]'
                '/best'
            ),
            'outtmpl': os.path.join(tmpdir, '%(title).150s.%(ext)s'),
            'merge_output_format': 'mp4',
            'ffmpeg_location': ffmpeg_path,
            'quiet': False,
            'no_warnings': True,
            'noplaylist': True,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
        }

        # Download and merge
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # If prepare_filename gave us intermediate file, find the merged MP4
        if not os.path.exists(filename):
            base, _ = os.path.splitext(filename)
            mp4_file = base + '.mp4'
            if os.path.exists(mp4_file):
                filename = mp4_file

        if not os.path.exists(filename):
            return jsonify({'error': 'Download selesai tapi file tidak ditemukan'}), 500

        # Send file to client
        @after_this_request
        def cleanup(response):
            if tmpdir and os.path.exists(tmpdir):
                shutil.rmtree(tmpdir, ignore_errors=True)
            return response

        basename = os.path.basename(filename)
        return send_file(
            filename,
            as_attachment=True,
            download_name=basename,
            mimetype='video/mp4'
        )

    except Exception as e:
        # Clean up on error
        if tmpdir and os.path.exists(tmpdir):
            shutil.rmtree(tmpdir, ignore_errors=True)
        
        error_msg = str(e)
        if '403' in error_msg or 'Forbidden' in error_msg:
            error_msg = 'Video tidak dapat diakses (403). Coba lagi atau gunakan yt-dlp lokal.'
        
        return jsonify({'error': error_msg}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
