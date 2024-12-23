import yt_dlp
import os
import logging
import subprocess
from flask import send_file
from handlers.download_state import download_progress
from handlers.video_handler import VideoHandler

logger = logging.getLogger(__name__)

class AudioHandler:
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir

    def get_audio_file(self, url):
        """Download audio directly"""
        try:
            # Create unique filenames for both temp files
            temp_id = os.urandom(8).hex()
            temp_video = os.path.join(self.temp_dir, f"{temp_id}_video.mp4")
            temp_audio = os.path.join(self.temp_dir, f"{temp_id}.mp3")
            
            # Get ffmpeg path
            ffmpeg_path = VideoHandler.check_ffmpeg()
            if not ffmpeg_path:
                raise Exception("FFmpeg not found. Please install FFmpeg to download audio.")

            # First download the video
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'outtmpl': temp_video,
                'progress_hooks': [self._progress_callback],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                download_progress['status'] = 'downloading'
                info = ydl.extract_info(url, download=True)
                filename = f"{info.get('title', 'audio')}.mp3"
                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()

                # Now convert to MP3 using ffmpeg directly
                download_progress['status'] = 'converting'
                download_progress['progress'] = 99

                if isinstance(ffmpeg_path, str):
                    ffmpeg_cmd = [
                        ffmpeg_path,
                        '-i', temp_video,
                        '-vn',  # No video
                        '-acodec', 'libmp3lame',
                        '-ab', '192k',
                        '-ar', '44100',
                        '-y',  # Overwrite output file
                        temp_audio
                    ]
                    
                    # Run ffmpeg
                    process = subprocess.Popen(
                        ffmpeg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    stdout, stderr = process.communicate()
                    
                    if process.returncode != 0:
                        logger.error(f"FFmpeg error: {stderr.decode()}")
                        raise Exception("Error converting to MP3")

                    # Clean up the video file
                    if os.path.exists(temp_video):
                        os.remove(temp_video)

                    # Verify the audio file exists
                    if not os.path.exists(temp_audio):
                        raise Exception("Failed to create MP3 file")

                    download_progress['progress'] = 100
                    download_progress['status'] = 'finished'
                    
                    return temp_audio, filename

        except Exception as e:
            logger.error(f"Error downloading/converting audio: {str(e)}")
            download_progress['status'] = 'error'
            # Clean up any temporary files
            for temp_file in [temp_video, temp_audio]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            raise

    def _progress_callback(self, d):
        """Internal progress callback for audio download"""
        try:
            if d['status'] == 'downloading':
                if 'total_bytes' in d:
                    download_progress['progress'] = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif 'total_bytes_estimate' in d:
                    download_progress['progress'] = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                download_progress['speed'] = d.get('speed', 0)
                download_progress['eta'] = d.get('eta', 0)
                download_progress['status'] = 'downloading'
                download_progress['started'] = True
            elif d['status'] == 'finished':
                download_progress['status'] = 'converting'
                download_progress['progress'] = 99
        except Exception as e:
            logger.error(f"Error in progress callback: {str(e)}")

    def create_audio_stream(self, file_path, filename):
        """Create an audio stream response"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise Exception("Downloaded file is empty")

            logger.info(f"Streaming audio file: {filename} ({file_size} bytes)")
            
            response = send_file(
                file_path,
                mimetype='audio/mpeg',
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
            logger.error(f"Error creating audio stream: {str(e)}")
            download_progress['status'] = 'error'
            download_progress['progress'] = 0
            if os.path.exists(file_path):
                os.remove(file_path)
            raise