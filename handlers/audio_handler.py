import os
import logging
import yt_dlp
from handlers.download_state import download_progress

logger = logging.getLogger(__name__)

class AudioHandler:
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir

    def get_audio_file(self, url, quality='best'):
        """Main method to handle audio download and conversion"""
        try:
            return self.download_audio(url, quality)
        except Exception as e:
            logger.error(f"Error in get_audio_file: {e}")
            download_progress['status'] = 'error'
            return None

    def create_audio_stream(self, file_path, chunk_size=8192):
        """Create a generator to stream the audio file
        
        Args:
            file_path (str): Path to the audio file
            chunk_size (int, optional): Size of chunks to read. Defaults to 8192.
        
        Yields:
            bytes: Chunks of the audio file
        """
        try:
            # Only try to convert chunk_size if it's not already an integer
            if not isinstance(chunk_size, int):
                try:
                    chunk_size = int(chunk_size)
                except (ValueError, TypeError):
                    # If conversion fails, use default chunk size
                    chunk_size = 8192
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    # Ensure we're yielding bytes
                    if not isinstance(chunk, bytes):
                        chunk = bytes(chunk)
                    yield chunk
        except Exception as e:
            logger.error(f"Error streaming audio file: {e}")
            # Return empty bytes instead of None for failed chunks
            yield b''

    def download_audio(self, url, quality='best'):
        """Download and convert audio from URL"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [self._progress_callback],
            # Use a temporary name first
            'outtmpl': os.path.join(self.temp_dir, 'temp_audio.%(ext)s'),
            'restrictfilenames': False,
            'windowsfilenames': False,
            'ignoreerrors': True,
            'noplaylist': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                download_progress['status'] = 'downloading'
                # Get video info first
                info = ydl.extract_info(url, download=True)
                video_title = info.get('title', '').strip()
                
                # Get the temporary file path
                temp_path = os.path.join(self.temp_dir, 'temp_audio.mp3')
                
                # Create the final filename with the exact video title
                final_filename = f"{video_title}.mp3"
                final_path = os.path.join(self.temp_dir, final_filename)
                
                # Rename the file if it exists
                if os.path.exists(temp_path):
                    if os.path.exists(final_path):
                        os.remove(final_path)  # Remove existing file if it exists
                    os.rename(temp_path, final_path)
                
                download_progress['status'] = 'finished'
                download_progress['progress'] = 100
                return final_path, final_filename
        except Exception as e:
            logger.error(f"Error in download_audio: {e}")
            download_progress['status'] = 'error'
            return None

    def _progress_callback(self, d):
        """Progress callback for audio download"""
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