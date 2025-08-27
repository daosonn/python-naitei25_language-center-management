import requests
import re

def get_youtube_video_duration_minutes(video_url):
    """
    Lấy thời lượng video YouTube (phút, làm tròn lên) từ URL video.
    Trả về int phút hoặc None nếu không lấy được.
    """
    # Lấy video id từ url
    match = re.search(r"(?:v=|youtu.be/)([\w-]{11})", video_url)
    if not match:
        return None
    video_id = match.group(1)
    # Gọi API không cần key (dùng oembed)
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        # Lấy thông tin video (oembed không có duration, chỉ có title/thumbnail)
        # Muốn lấy duration phải dùng YouTube Data API (cần API key), hoặc parse trang web
        # Ở đây sẽ thử parse trang web
        html = requests.get(f"https://www.youtube.com/watch?v={video_id}").text
        match = re.search(r'"approxDurationMs":"(\d+)"', html)
        if match:
            ms = int(match.group(1))
            minutes = (ms + 59999) // 60000  # Làm tròn lên phút
            return minutes
    except Exception:
        pass
    return None
