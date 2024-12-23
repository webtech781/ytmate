import yt_dlp
import logging
import os
import tempfile
import subprocess
from flask import send_file
from handlers.download_state import download_progress

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
    def download_video(url, quality='best', progress_hook=None):
        """Download video and return path to downloaded file"""
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'video.mp4')
        
        ffmpeg_path = VideoHandler.check_ffmpeg()
        format_str = VideoHandler.get_format_string(quality, bool(ffmpeg_path))
        
        ydl_opts = {
            'format': format_str,
            'quiet': True,
            'progress_hooks': [progress_hook] if progress_hook else None,
            'outtmpl': temp_file,
            'no_warnings': True,
        }

        if isinstance(ffmpeg_path, str):
            ydl_opts.update({
                'ffmpeg_location': os.path.dirname(ffmpeg_path),
                'merge_output_format': 'mp4'
            })
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Update progress to indicate download is starting
                if progress_hook:
                    progress_hook({'status': 'starting', 'downloaded_bytes': 0, 'total_bytes': 0})
                
                info = ydl.extract_info(url, download=True)
                
                # Update progress to indicate download is complete
                if progress_hook:
                    progress_hook({'status': 'finished', 'downloaded_bytes': 100, 'total_bytes': 100})
                
                filename = f"{info.get('title', 'video')}_{quality}.mp4"
                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                
                file_size = os.path.getsize(temp_file)
                logger.info(f"Downloaded video: {filename} ({file_size} bytes)")
                
                return temp_file, filename

        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            download_progress['status'] = 'error'
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise

    @staticmethod
    def create_video_stream(file_path, filename):
        """Create a video stream response"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Video file not found: {file_path}")

            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise Exception("Downloaded file is empty")

            logger.info(f"Streaming file: {filename} ({file_size} bytes)")
            
            response = send_file(
                file_path,
                mimetype='video/mp4',
                as_attachment=True,
                download_name=filename
            )

            @response.call_on_close
            def cleanup():
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Cleaned up temporary file: {file_path}")
                except Exception as e:
                    logger.error(f"Error cleaning up file: {str(e)}")

            return response

        except Exception as e:
            logger.error(f"Error creating video stream: {str(e)}")
            download_progress['status'] = 'error'
            download_progress['progress'] = 0
            if os.path.exists(file_path):
                os.remove(file_path)
            raise