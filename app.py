from flask import Flask, request, jsonify, send_file, render_template, abort, Response
from flask_cors import CORS
import yt_dlp
import os
import moviepy.editor as mp
import logging
from pathlib import Path
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

FFMPEG_PATH = os.path.join(os.path.dirname(__file__), "bin", "ffmpeg.exe")

def check_ffmpeg():
    if not os.path.exists(FFMPEG_PATH):
        logger.warning(f"FFmpeg not found at {FFMPEG_PATH}. MP3 conversion will not work.")
        return False
    return True

check_ffmpeg()

def get_video_info_from_url(url):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        return {
            'title': info.get('title', 'Unknown Title'),
            'author': info.get('uploader', 'Unknown Author'),
            'thumbnail_url': info.get('thumbnail', ''),
            'duration': info.get('duration', 0),
            'views': info.get('view_count', 0)
        }
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        raise

def download_progress_hook(d):
    if d['status'] == 'downloading':
        try:
            progress = float(d['downloaded_bytes']) / float(d['total_bytes']) * 100
            logger.info(f"Download progress: {progress:.1f}%")
            app.config['DOWNLOAD_PROGRESS'] = {
                'progress': progress,
                'speed': d.get('speed', 0),
                'eta': d.get('eta', 0),
                'status': 'downloading'
            }
        except:
            pass
    elif d['status'] == 'finished':
        logger.info("Download completed")
        app.config['DOWNLOAD_PROGRESS'] = {
            'progress': 100,
            'status': 'converting'
        }

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/api/video-info', methods=['GET'])
def get_video_info():
    try:
        video_url = request.args.get('url')
        logger.info(f"Fetching info for URL: {video_url}")
        
        video_info = get_video_info_from_url(video_url)
        
        logger.info(f"Successfully fetched video info: {video_info}")
        return jsonify(video_info)
        
    except Exception as e:
        logger.error(f"Error fetching video info: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400

@app.route('/api/download', methods=['GET'])
def download_video():
    try:
        app.config['DOWNLOAD_PROGRESS'] = {
            'progress': 0,
            'status': 'starting'
        }
        
        video_url = request.args.get('url')
        format_type = request.args.get('format', 'mp4')
        
        if format_type == 'mp3' and not check_ffmpeg():
            return jsonify({'error': 'FFmpeg not installed. Please install FFmpeg to download MP3s.'}), 400
        
        logger.info(f"Starting download for URL: {video_url} in format: {format_type}")
        
        # Get video info
        info = get_video_info_from_url(video_url)
        filename = f"{info['title']}_{format_type}"
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        if format_type == 'mp4':
            logger.info("Downloading MP4...")
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, f'{filename}.%(ext)s'),
                'progress_hooks': [download_progress_hook],
            }
            
        elif format_type == 'mp3':
            logger.info("Downloading and converting to MP3...")
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, f'{filename}.%(ext)s'),
                'progress_hooks': [download_progress_hook],
                'ffmpeg_location': FFMPEG_PATH,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        output_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.{format_type}")
        logger.info(f"Download completed: {output_path}")
        
        app.config['DOWNLOAD_PROGRESS'] = {
            'progress': 100,
            'status': 'finished'
        }
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{filename}.{format_type}"
        )
        
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}", exc_info=True)
        app.config['DOWNLOAD_PROGRESS'] = {
            'progress': 0,
            'status': 'error',
            'error': str(e)
        }
        return jsonify({'error': str(e)}), 400

@app.route('/api/progress')
def get_progress():
    progress_data = app.config.get('DOWNLOAD_PROGRESS', {
        'progress': 0,
        'status': 'waiting'
    })
    return jsonify(progress_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000) 