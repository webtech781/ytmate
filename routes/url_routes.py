from flask import jsonify, request, session, send_from_directory, render_template
import yt_dlp
import logging
import threading
import os
import tempfile
from pathlib import Path
import os
import tempfile
from pathlib import Path
from handlers.video_handler import VideoHandler
from handlers.audio_handler import AudioHandler
from handlers.download_state import download_progress
from yt_dlp.cookies import extract_cookies_from_browser
import json
import re
import requests
from urllib.parse import parse_qs, urlparse
from utils.youtube import get_video_id
import time

logger = logging.getLogger(__name__)

def progress_hook(d):
    block_size = 8192  # Define block size constant
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
        elif d['status'] == 'finished' or d.get('downloaded_bytes', 0) >= d.get('total_bytes', 0) - block_size:
            download_progress['progress'] = 100
            download_progress['speed'] = 0
            download_progress['eta'] = 0
            download_progress['status'] = 'finished'
            download_progress['started'] = False
            time.sleep(0.5)
    except Exception as e:
        logger.error(f"Error in progress hook: {str(e)}")
        download_progress['status'] = 'error'

def get_cookie_file():
    """Get platform-independent path for cookie file"""
    cookie_dir = os.path.join(tempfile.gettempdir(), 'ytmate_cookies')
    os.makedirs(cookie_dir, exist_ok=True)
    return os.path.join(cookie_dir, 'youtube.txt')

def get_video_info_direct(video_id):
    """Get video info using YouTube's Innertube API"""
    url = "https://www.youtube.com/youtubei/v1/player"
    params = {
        "key": "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
    }
    data = {
        "context": {
            "client": {
                "hl": "en",
                "gl": "US",
                "clientName": "WEB",
                "clientVersion": "2.20231219.01.00",
                "originalUrl": f"https://www.youtube.com/watch?v={video_id}",
                "platform": "DESKTOP"
            }
        },
        "videoId": video_id,
        "playbackContext": {
            "contentPlaybackContext": {
                "signatureTimestamp": "19719"
            }
        }
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Content-Type": "application/json",
        "X-YouTube-Client-Name": "1",
        "X-YouTube-Client-Version": "2.20231219.01.00",
        "Origin": "https://www.youtube.com"
    }
    
    response = requests.post(url, params=params, json=data, headers=headers)
    response.raise_for_status()
    return response.json()

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
                response, filename = VideoHandler.download_video(video_url, quality, progress_hook)
                return response
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
            
            video_id = get_video_id(video_url)
            if not video_id:
                raise ValueError("Invalid YouTube URL")
                
            data = get_video_info_direct(video_id)
            logger.debug(f"API Response: {json.dumps(data.get('videoDetails', {}), indent=2)}")
            
            video_details = data.get('videoDetails', {})
            thumbnails = video_details.get('thumbnail', {}).get('thumbnails', [{}])
            thumbnail_url = thumbnails[0].get('url', '')
            
            return jsonify({
                'title': video_details.get('title', 'Unknown Title'),
                'author': video_details.get('author', video_details.get('channelTitle', 'Unknown Author')),
                'thumbnail_url': thumbnail_url,
                'duration': int(video_details.get('lengthSeconds', 0)),
                'views': int(video_details.get('viewCount', 0))
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
