from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp
import requests  # Import library baru ini

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_video_info():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL tidak boleh kosong'}), 400

    # Opsi yt-dlp
    ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
    'outtmpl': output_template,
    'merge_output_format': 'mp4',
    'ffmpeg_location': '/home/quic1934/ffmpeg/ffmpeg-7.0.2-amd64-static',
    'quiet': True,
    'no_warnings': True,
}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_data = {
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string'),
                'url': info.get('url'), # Ini URL asli dari Google
                'ext': info.get('ext')
            }
            return jsonify(video_data)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- TAMBAHKAN BAGIAN INI ---
@app.route('/download_proxy')
def download_proxy():
    file_url = request.args.get('url')
    title = request.args.get('title', 'video')
    ext = request.args.get('ext', 'mp4')
    
    if not file_url:
        return "URL tidak ditemukan", 400

    # Server mendownload file dari Google secara streaming
    req = requests.get(file_url, stream=True)

    # Server meneruskan (pipe) data langsung ke user
    return Response(
        stream_with_context(req.iter_content(chunk_size=1024)),
        content_type=req.headers['content-type'],
        headers={
            'Content-Disposition': f'attachment; filename="{title}.{ext}"'
        }
    )
# ----------------------------

if __name__ == '__main__':
    app.run(debug=True, port=5000)