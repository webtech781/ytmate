from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp
import logging
import os
import requests
import tempfile
import threading
import time
import shutil

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Create a temporary directory for processing
TEMP_DIR = tempfile.mkdtemp()
logger.info(f"Created temporary directory: {TEMP_DIR}")

def cleanup_temp_file(filepath, delay=300):  # 300 seconds = 5 minutes
    """Delete temporary file after specified delay"""
    def delete_file():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted temporary file: {filepath}")
        except Exception as e:
            logger.error(f"Error deleting temporary file: {str(e)}")

    thread = threading.Thread(target=delete_file)
    thread.daemon = True
    thread.start()

def get_direct_url(url, format_type):
    try:
        if format_type == 'mp4':
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info['url'], info.get('title', 'video')
        else:  # MP3
            temp_file = os.path.join(TEMP_DIR, f"{time.time()}.mp3")
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'outtmpl': temp_file,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                cleanup_temp_file(temp_file)  # Schedule file deletion
                return temp_file, info.get('title', 'audio')
                
    except Exception as e:
        logger.error(f"Error getting direct URL: {str(e)}")
        raise

@app.route('/api/download', methods=['GET'])
def download_video():
    try:
        video_url = request.args.get('url')
        format_type = request.args.get('format', 'mp4')
        
        file_path, title = get_direct_url(video_url, format_type)
        
        # Clean filename
        filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{filename}.{format_type}"

        def generate():
            if format_type == 'mp4':
                # Stream video directly
                with requests.get(file_path, stream=True) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk
            else:
                # Stream MP3 from temporary file
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        yield chunk

        response = Response(stream_with_context(generate()))
        response.headers.set('Content-Disposition', 'attachment', filename=filename)
        response.headers.set('Content-Type', 'application/octet-stream')
        return response

    except Exception as e:
        logger.error(f"Error downloading: {str(e)}")
        return jsonify({'error': str(e)}), 400

# Clean up temporary directory on shutdown
@app.teardown_appcontext
def cleanup_temp_dir(error):
    try:
        shutil.rmtree(TEMP_DIR)
        logger.info(f"Cleaned up temporary directory: {TEMP_DIR}")
    except Exception as e:
        logger.error(f"Error cleaning up temporary directory: {str(e)}")

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
        logger.error(f"Error fetching video info: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/progress')
def get_progress():
    return jsonify({
        'progress': 0,
        'status': 'streaming'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=5000) 