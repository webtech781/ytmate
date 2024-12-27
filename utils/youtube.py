from urllib.parse import parse_qs, urlparse

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    parsed = urlparse(url)
    if parsed.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed.path[1:]
    if parsed.hostname in ('youtube.com', 'www.youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query)['v'][0]
        if parsed.path.startswith(('/embed/', '/v/', '/shorts/')):
            return parsed.path.split('/')[2]
    return None 