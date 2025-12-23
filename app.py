from flask import Flask, render_template, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import yt_dlp
import requests
import re
import os
import shutil
import tempfile
import time

app = Flask(__name__)
CORS(app)

# Enhanced yt-dlp options to bypass 403 errors
def get_ydl_opts(download=False, tmpdir=None, ffmpeg_path=None):
    """Get enhanced yt-dlp options with anti-403 measures."""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'socket_timeout': 30,
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'ignoreerrors': False,
        'nocheckcertificate': True,
        'age_limit': None,
        'extractor_retries': 3,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Connection': 'keep-alive',
        },
        'cookiesfrombrowser': None,
    }
    
    if download and tmpdir and ffmpeg_path:
        opts.update({
            'format': (
                'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/'
                'bestvideo[ext=mp4]+bestaudio[ext=m4a]/'
                'best[ext=mp4][height<=1080]/'
                'best[ext=mp4]/'
                'best'
            ),
            'outtmpl': os.path.join(tmpdir, '%(title).150s.%(ext)s'),
            'merge_output_format': 'mp4',
            'ffmpeg_location': ffmpeg_path,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        })
    
    return opts


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
        ydl_opts = get_ydl_opts(download=False)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return jsonify({
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string') or str(info.get('duration', 0)),
                'uploader': info.get('uploader', ''),
                'view_count': info.get('view_count', 0),
            })
    except Exception as e:
        error_msg = str(e)
        if '403' in error_msg or 'Forbidden' in error_msg:
            error_msg = 'Video tidak dapat diakses (403). Pastikan URL valid dan video tersedia.'
        return jsonify({'error': error_msg}), 500


@app.route('/api/formats', methods=['POST'])
def get_video_formats():
    """Get available video formats/qualities."""
    data = request.get_json(silent=True) or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'URL tidak boleh kosong'}), 400

    try:
        ydl_opts = get_ydl_opts(download=False)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract unique video formats with audio
            formats_dict = {}
            
            for f in info.get('formats', []):
                # Only consider formats with video
                if f.get('vcodec') != 'none' and f.get('height'):
                    height = f.get('height')
                    ext = f.get('ext', 'mp4')
                    filesize = f.get('filesize') or f.get('filesize_approx') or 0
                    
                    # Create quality label
                    quality = f"{height}p"
                    
                    # Keep highest bitrate for each resolution
                    if quality not in formats_dict or filesize > formats_dict[quality].get('filesize', 0):
                        formats_dict[quality] = {
                            'quality': quality,
                            'height': height,
                            'ext': ext,
                            'filesize': filesize,
                            'filesize_mb': round(filesize / (1024 * 1024), 1) if filesize else None,
                            'format_note': f.get('format_note', ''),
                        }
            
            # Sort by resolution
            formats_list = sorted(
                formats_dict.values(),
                key=lambda x: x['height'],
                reverse=True
            )
            
            return jsonify({
                'formats': formats_list,
                'title': info.get('title', 'Unknown'),
            })
            
    except Exception as e:
        error_msg = str(e)
        if '403' in error_msg or 'Forbidden' in error_msg:
            error_msg = 'Video tidak dapat diakses (403). Pastikan URL valid dan video tersedia.'
        return jsonify({'error': error_msg}), 500


@app.route('/api/download', methods=['POST'])
def api_download():
    """Download video using yt-dlp with enhanced 403 bypass."""
    # Support both JSON and form data
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form.to_dict()
    
    url = data.get('url', '').strip()
    quality = data.get('quality', 'best')  # Get quality parameter

    if not url:
        return jsonify({'error': 'URL tidak boleh kosong'}), 400

    ffmpeg_path = _get_ffmpeg()
    if not ffmpeg_path:
        return jsonify({'error': 'ffmpeg tidak tersedia di server. Gunakan yt-dlp lokal.'}), 503

    tmpdir = None
    try:
        # Create temp directory for download
        tmpdir = tempfile.mkdtemp(prefix='ytdlp_')

        # Get enhanced options
        ydl_opts = get_ydl_opts(download=True, tmpdir=tmpdir, ffmpeg_path=ffmpeg_path)
        
        # Update format based on quality selection
        if quality and quality != 'best':
            # Extract resolution number (e.g., '720p' -> 720)
            try:
                height = int(quality.replace('p', ''))
                ydl_opts['format'] = (
                    f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/'
                    f'bestvideo[height<={height}]+bestaudio/'
                    f'best[height<={height}][ext=mp4]/'
                    f'best[height<={height}]/'
                    f'best'
                )
            except ValueError:
                pass  # Use default format if parsing fails
        
        # Add additional bypass options for stubborn 403s
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['android', 'web'],
                'player_skip': ['configs', 'webpage']
            }
        }

        # Download with retry logic
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                
                # If prepare_filename gave us intermediate file, find the merged MP4
                if not os.path.exists(filename):
                    base, _ = os.path.splitext(filename)
                    mp4_file = base + '.mp4'
                    if os.path.exists(mp4_file):
                        filename = mp4_file
                    else:
                        # Find any mp4 file in tmpdir
                        for f in os.listdir(tmpdir):
                            if f.endswith('.mp4'):
                                filename = os.path.join(tmpdir, f)
                                break
                
                if os.path.exists(filename):
                    # Success! Send file
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
                else:
                    last_error = 'File tidak ditemukan setelah download'
                    
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                break

        # If we get here, all retries failed
        if tmpdir and os.path.exists(tmpdir):
            shutil.rmtree(tmpdir, ignore_errors=True)
        
        if '403' in str(last_error) or 'Forbidden' in str(last_error):
            return jsonify({
                'error': '⚠️ Video diblokir oleh YouTube (403).\n\n'
                         'Solusi:\n'
                         '1. Coba lagi dalam beberapa menit\n'
                         '2. Update yt-dlp: pip install -U yt-dlp\n'
                         '3. Gunakan yt-dlp lokal di komputer Anda'
            }), 403
        
        return jsonify({'error': f'Download gagal: {last_error}'}), 500

    except Exception as e:
        # Clean up on error
        if tmpdir and os.path.exists(tmpdir):
            shutil.rmtree(tmpdir, ignore_errors=True)
        
        error_msg = str(e)
        if '403' in error_msg or 'Forbidden' in error_msg:
            error_msg = '⚠️ Video tidak dapat diakses (403). Update yt-dlp atau coba lagi nanti.'
        
        return jsonify({'error': error_msg}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
