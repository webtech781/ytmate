# YTMate - YouTube Video Downloader

YTMate is a modern, user-friendly YouTube video downloader built with Python and Flask. It allows users to download videos in both MP4 and MP3 formats with a clean, responsive interface.

![YTMate Screenshot](screenshot.png)

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
pip install -r requirements.txt
```


4. Make sure FFmpeg is installed and accessible in your system PATH

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

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/improvement`)
6. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for the YouTube download functionality
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [FFmpeg](https://ffmpeg.org/) for media processing

## Support

If you encounter any issues or have questions, please:
1. Check the [Issues](https://github.com/yourusername/ytmate/issues) page
2. Create a new issue if your problem isn't already listed

## Security

Please note that this tool is for personal use only. Respect YouTube's terms of service and copyright laws when downloading content.
