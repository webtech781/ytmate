from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp
import logging
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

FFMPEG_PATH = os.path.join(os.path.dirname(__file__), "bin", "ffmpeg.exe")

def check_ffmpeg():
    if not os.path.exists(FFMPEG_PATH):
        logger.warning(f"FFmpeg not found at {FFMPEG_PATH}. MP3 conversion will not work.")
        return False
    return True

def stream_video(url, format_type):
    try:
        if format_type == 'mp4':
            ydl_opts = {
                'format': 'best[ext=mp4]',
            }
        elif format_type == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'ffmpeg_location': FFMPEG_PATH,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if format_type == 'mp4':
                url = info['url']
            else:
                # For MP3, get the best audio format URL
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        url = f['url']
                        break

            # Stream the content
            def generate():
                import requests
                response = requests.get(url, stream=True)
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        yield chunk

            return generate(), info.get('title', 'video')
    except Exception as e:
        logger.error(f"Error streaming video: {str(e)}")
        raise

@app.route('/api/download', methods=['GET'])
def download_video():
    try:
        video_url = request.args.get('url')
        format_type = request.args.get('format', 'mp4')
        
        if format_type == 'mp3' and not check_ffmpeg():
            return jsonify({'error': 'FFmpeg not installed. Please install FFmpeg to download MP3s.'}), 400

        generator, title = stream_video(video_url, format_type)
        
        # Clean filename
        filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{filename}.{format_type}"

        response = Response(stream_with_context(generator()))
        response.headers.set('Content-Disposition', 'attachment', filename=filename)
        response.headers.set('Content-Type', 'application/octet-stream')
        return response

    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/api/video-info', methods=['GET'])
def get_video_info():
    try:
        video_url = request.args.get('url')
        logger.info(f"Fetching info for URL: {video_url}")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
        return jsonify({
            'title': info.get('title', 'Unknown Title'),
            'author': info.get('uploader', 'Unknown Author'),
            'thumbnail_url': info.get('thumbnail', ''),
            'duration': info.get('duration', 0),
            'views': info.get('view_count', 0)
        })
        
    except Exception as e:
        logger.error(f"Error fetching video info: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400

@app.route('/api/progress')
def get_progress():
    progress_data = app.config.get('DOWNLOAD_PROGRESS', {
        'progress': 0,
        'status': 'waiting'
    })
    return jsonify(progress_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=5000) 