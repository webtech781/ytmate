mkdir youtube_downloader
cd youtube_downloader
python -m venv venv

# Create necessary directories
mkdir static
mkdir handlers

# Activate the virtual environment (Windows)
# venv\Scripts\activate

# Activate the virtual environment (Linux/Mac)
# source venv/bin/activate

# Install requirements
pip install flask flask-cors yt-dlp requests

# Create an empty __init__.py in handlers directory
touch handlers/__init__.py

# Install ffmpeg
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get update
    sudo apt-get install -y ffmpeg
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew install ffmpeg
else
    # For Windows, download and install ffmpeg
    echo "Please install ffmpeg manually on Windows from: https://www.gyan.dev/ffmpeg/builds/"
    echo "Download ffmpeg-git-full.7z, extract it, and add the bin folder to your system PATH"
fi