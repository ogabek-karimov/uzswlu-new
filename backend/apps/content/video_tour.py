"""Video tur havolasini tekshirish: faqat YouTube, Vimeo yoki to'g'ridan-to'g'ri https video fayl (mp4/webm/ogg)."""
import re
from urllib.parse import urlparse

YOUTUBE = re.compile(r'^https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|live/)|youtu\.be/)([\w-]{11})(?:[?&#/]|$)')
VIMEO = re.compile(r'^https?://(?:www\.|player\.)?vimeo\.com/(?:video/)?(\d{6,12})(?:[?&#/]|$)')
FILE_EXT = ('.mp4', '.webm', '.ogg')


def parse_video(url: str) -> tuple[str, str] | None:
    """-> (tur, ko'mish manzili) yoki None: tur = youtube | vimeo | file."""
    url = (url or '').strip()
    if m := YOUTUBE.match(url):
        return 'youtube', f'https://www.youtube-nocookie.com/embed/{m.group(1)}?rel=0&autoplay=1'
    if m := VIMEO.match(url):
        return 'vimeo', f'https://player.vimeo.com/video/{m.group(1)}?autoplay=1&dnt=1'
    parts = urlparse(url)
    if parts.scheme == 'https' and parts.netloc and parts.path.lower().endswith(FILE_EXT):
        return 'file', url
    return None
