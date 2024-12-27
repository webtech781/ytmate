import yt_dlp
import logging
import os
import subprocess
from flask import Response, stream_with_context
from handlers.download_state import download_progress
import requests
from utils.youtube import get_video_id

logger = logging.getLogger(__name__)

class VideoHandler:
    @staticmethod
    def check_ffmpeg():
        """Check if ffmpeg is installed or available in current directory"""
        try:
            # First try the system PATH
            subprocess.run(['ffmpeg', '-version'], capture_output=True)
            return True
        except FileNotFoundError:
            try:
                # Try current directory
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                ffmpeg_path = os.path.join(project_root, 'ffmpeg', 'bin', 'ffmpeg.exe')
                
                if os.path.exists(ffmpeg_path):
                    # Test if the ffmpeg executable works
                    subprocess.run([ffmpeg_path, '-version'], capture_output=True)
                    logger.info(f"Found ffmpeg at: {ffmpeg_path}")
                    return ffmpeg_path
            except Exception as e:
                logger.error(f"Error checking local ffmpeg: {str(e)}")
            return False

    @staticmethod
    def get_format_string(quality='best', has_ffmpeg=False):
        """Get the appropriate format string based on quality and ffmpeg availability"""
        if not has_ffmpeg:
            # Without ffmpeg, we need formats that don't require merging
            quality_formats = {
                '2160p': 'best[height<=2160][ext=mp4][acodec!=none][vcodec!=none]',
                '1440p': 'best[height<=1440][ext=mp4][acodec!=none][vcodec!=none]',
                '1080p': 'best[height<=1080][ext=mp4][acodec!=none][vcodec!=none]',
                '720p': 'best[height<=720][ext=mp4][acodec!=none][vcodec!=none]',
                '480p': 'best[height<=480][ext=mp4][acodec!=none][vcodec!=none]',
                '360p': 'best[height<=360][ext=mp4][acodec!=none][vcodec!=none]',
                'best': 'best[ext=mp4][acodec!=none][vcodec!=none]/best'
            }
        else:
            # With ffmpeg, we can merge separate video and audio streams
            quality_formats = {
                '2160p': 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]',
                '1440p': 'bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440]',
                '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]',
                '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
                '480p': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]',
                '360p': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]',
                'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            }
        
        return quality_formats.get(quality, quality_formats['best'])

    @staticmethod
    def get_available_formats(url):
        """Get available video formats"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                
                has_ffmpeg = VideoHandler.check_ffmpeg()
                available_qualities = []
                seen_heights = set()
                
                for f in formats:
                    # Only include formats that have both video and audio if ffmpeg is not available
                    if not has_ffmpeg and (f.get('acodec') == 'none' or f.get('vcodec') == 'none'):
                        continue
                        
                    if f.get('ext') == 'mp4' and f.get('height'):
                        height = f.get('height')
                        if height not in seen_heights:
                            seen_heights.add(height)
                            available_qualities.append({
                                'height': height,
                                'quality': f"{height}p",
                                'filesize': f.get('filesize', 'Unknown')
                            })
                
                # Always include 'best' option
                if 'best' not in [q['quality'] for q in available_qualities]:
                    available_qualities.append({
                        'height': 0,
                        'quality': 'best',
                        'filesize': 'Unknown'
                    })
                
                return sorted(available_qualities, key=lambda x: x['height'], reverse=True)
        except Exception as e:
            logger.error(f"Error getting formats: {str(e)}")
            raise

    @staticmethod
    def get_ydl_opts(quality='best', progress_callback=None):
        ydl_opts = {
            'format': quality,
            'outtmpl': '%(title)s.%(ext)s',
            'progress_hooks': [progress_callback] if progress_callback else None,
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 5,
            'extractor_retries': 5,
            'file_access_retries': 5,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate'
            }
        }
        return ydl_opts

    @staticmethod
    def get_video_url(video_id, quality='best'):
        """Get direct video URL using Innertube API"""
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
        data = response.json()
        
        formats = data.get('streamingData', {}).get('formats', [])
        formats.extend(data.get('streamingData', {}).get('adaptiveFormats', []))
        
        # Sort by quality and pick the best matching format
        formats.sort(key=lambda x: int(x.get('height', 0)), reverse=True)
        for fmt in formats:
            if fmt.get('mimeType', '').startswith('video/mp4'):
                return fmt['url'], data['videoDetails']['title']
                
        raise Exception("No suitable format found")

    @staticmethod
    def download_video(url, quality='best', progress_callback=None):
        """Stream video directly to client"""
        try:
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'socket_timeout': 30,
                'retries': 5,
                'fragment_retries': 5,
                'extractor_retries': 5,
                'file_access_retries': 5,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Origin': 'https://www.youtube.com',
                    'Referer': 'https://www.youtube.com/'
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info['url']
                title = info['title']
                filename = f"{title}_{quality}.mp4"
                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()

                def generate():
                    headers = {
                        'User-Agent': ydl_opts['http_headers']['User-Agent'],
                        'Accept': '*/*',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Origin': 'https://www.youtube.com',
                        'Referer': 'https://www.youtube.com/',
                        'Sec-Fetch-Dest': 'video',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Site': 'cross-site',
                        'Range': 'bytes=0-'  # Add range header for streaming
                    }

                    with requests.get(video_url, stream=True, headers=headers) as r:
                        r.raise_for_status()
                        total_size = int(r.headers.get('content-length', 0))
                        block_size = 8192
                        downloaded = 0

                        for chunk in r.iter_content(chunk_size=block_size):
                            if chunk:
                                downloaded += len(chunk)
                                if progress_callback and total_size:
                                    progress_callback({
                                        'status': 'downloading',
                                        'downloaded_bytes': downloaded,
                                        'total_bytes': total_size,
                                        'speed': block_size
                                    })
                                yield chunk

                response = Response(
                    stream_with_context(generate()),
                    content_type='video/mp4'
                )
                response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response, filename

        except Exception as e:
            logger.error(f"Error streaming video: {str(e)}")
            if progress_callback:
                progress_callback({'status': 'error'})
            raise
