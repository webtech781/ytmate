from flask import jsonify, request, session, send_from_directory, render_template
import yt_dlp
import logging
import threading
from handlers.video_handler import VideoHandler
from handlers.audio_handler import AudioHandler
from handlers.download_state import download_progress

logger = logging.getLogger(__name__)

def progress_hook(d):
    try:
        if d['status'] == 'starting':
            download_progress['started'] = True
            download_progress['progress'] = 0
            download_progress['status'] = 'starting'
            download_progress['speed'] = 0
            download_progress['eta'] = 0
        elif d['status'] == 'downloading':
            download_progress['started'] = True
            if 'total_bytes' in d:
                download_progress['progress'] = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif 'total_bytes_estimate' in d:
                download_progress['progress'] = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            download_progress['speed'] = d.get('speed', 0)
            download_progress['eta'] = d.get('eta', 0)
            download_progress['status'] = 'downloading'
        elif d['status'] == 'finished':
            download_progress['progress'] = 100
            download_progress['speed'] = 0
            download_progress['eta'] = 0
            download_progress['status'] = 'finished'
    except Exception as e:
        logger.error(f"Error in progress hook: {str(e)}")
        download_progress['status'] = 'error'

def init_routes(app, TEMP_DIR):
    @app.route('/api/download', methods=['GET'])
    def download_video():
        try:
            download_progress['progress'] = 0
            download_progress['status'] = 'starting'
            download_progress['speed'] = 0
            download_progress['eta'] = 0
            download_progress['started'] = False

            video_url = request.args.get('url')
            format_type = request.args.get('format', 'mp4')
            quality = request.args.get('quality', 'best')
            
            if format_type == 'mp4':
                file_path, filename = VideoHandler.download_video(video_url, quality, progress_hook)
                return VideoHandler.create_video_stream(file_path, filename)
            else:
                audio_handler = AudioHandler(TEMP_DIR)
                file_path, filename = audio_handler.get_audio_file(video_url)
                return audio_handler.create_audio_stream(file_path, filename)

        except Exception as e:
            logger.error(f"Error downloading: {str(e)}")
            download_progress['status'] = 'error'
            return jsonify({'error': str(e)}), 400

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
        return jsonify(download_progress)

    @app.route('/api/formats', methods=['GET'])
    def get_video_formats():
        try:
            video_url = request.args.get('url')
            formats = VideoHandler.get_available_formats(video_url)
            return jsonify(formats)
        except Exception as e:
            logger.error(f"Error getting formats: {str(e)}")
            return jsonify({'error': str(e)}), 400

    @app.route('/api/check-ffmpeg')
    def check_ffmpeg():
        has_ffmpeg = VideoHandler.check_ffmpeg()
        return jsonify({'ffmpeg_installed': has_ffmpeg})