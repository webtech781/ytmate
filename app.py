from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp
import logging
import os
import requests

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

def get_direct_url(url, format_type):
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]' if format_type == 'mp4' else 'bestaudio/best',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if format_type == 'mp4':
                # Get direct video URL
                return info['url'], info.get('title', 'video')
            else:
                # Get direct audio URL
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        return f['url'], info.get('title', 'audio')
                
        raise Exception('No suitable format found')
    except Exception as e:
        logger.error(f"Error getting direct URL: {str(e)}")
        raise

@app.route('/api/download', methods=['GET'])
def download_video():
    try:
        video_url = request.args.get('url')
        format_type = request.args.get('format', 'mp4')
        
        direct_url, title = get_direct_url(video_url, format_type)
        
        # Clean filename
        filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{filename}.{format_type}"

        def generate():
            with requests.get(direct_url, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

        response = Response(stream_with_context(generate()))
        response.headers.set('Content-Disposition', 'attachment', filename=filename)
        response.headers.set('Content-Type', 'application/octet-stream')
        return response

    except Exception as e:
        logger.error(f"Error downloading: {str(e)}")
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