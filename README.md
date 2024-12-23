# YTMate - YouTube Video Downloader

YTMate is a modern, user-friendly YouTube video downloader built with Python and Flask. It allows users to download videos in both MP4 and MP3 formats with a clean, responsive interface.

![YTMate Screenshot](/img/screenshot.png)

## Features

- 🎥 Download YouTube videos in MP4 format
- 🎵 Convert and download videos as MP3
- 🎨 Clean, modern interface
- 📱 Fully responsive design
- 📊 Real-time download progress tracking
- 🔍 Video preview with thumbnail and details
- ⚡ Fast downloads using yt-dlp

## Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg (for MP3 conversion)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/webtech781/ytmate.git
cd ytmate
```

2. Create and activate a virtual environment:

Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```

macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
# For Windows (use this since you're on Windows)
python -m pip install -r requirements.txt

# Or simply
pip install -r requirements.txt
```



4. Install FFmpeg:
   - **Windows**: Download from [ffmpeg.org](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip) and extract it. Copy the `bin` folder from the extracted files and paste it into the `ffmpeg` directory within the project folder, renaming it to `ffmpeg`.
   - **Linux**: `sudo apt-get install ffmpeg`
   - **Mac**: `brew install ffmpeg`

## Project Structure

youtube_downloader/

├── static/ # Static files

│ ├── index.html # Main page

│ └── style.css # Styles

├── templates/ # Flask templates

│ └── error.html # Error page

├── handlers/ # Backend handlers

│ ├── init.py

│ ├── audio_handler.py

│ ├── video_handler.py

│ └── download_state.py

├── routes/ # Flask routes

│ ├── init.py

│ ├── static_routes.py

│ └── url_routes.py

├── app.py # Main application file

└── requirements.txt # Python dependencies

## Usage

1. Start the application:

```bash
python app.py
```

2. Open your web browser and navigate to:

```
http://localhost:5000
```


3. Enter a YouTube URL and select your preferred format (MP4 or MP3)

4. Click Download and wait for the process to complete

## Configuration

You can modify the following settings in `config.py`:
- Download directory
- Supported formats
- Quality preferences
- Other application settings


3. Paste a YouTube URL and choose your preferred format:
   - Click "Download MP4" for video
   - Click "Download MP3" for audio only

## Features in Detail

### Video Download
- Multiple quality options (up to 4K if available)
- Progress tracking with speed and ETA
- Automatic format selection based on quality
- Proper filename handling

### Audio Extraction
- High-quality MP3 conversion
- Metadata preservation
- Progress tracking during download and conversion

### Error Handling
- Invalid URL detection
- Network error handling
- User-friendly error messages
- Automatic cleanup of temporary files

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube download functionality
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [FFmpeg](https://ffmpeg.org/) for media processing

## Support

For support, please open an issue in the GitHub repository or contact [Email](vamsikrishna781@proton.me) .

## Disclaimer

This tool is for personal use only. Please respect YouTube's terms of service and copyright laws when using this application.
