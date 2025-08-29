import pytest
from courses.utils_youtube import get_youtube_video_duration_minutes
from unittest import mock

@mock.patch('courses.utils_youtube.requests.get')
def test_get_youtube_video_duration_minutes_success(mock_get):
    # Giả lập HTML có approxDurationMs
    mock_get.return_value.text = '{"approxDurationMs":"125000"}'
    url = 'https://www.youtube.com/watch?v=abcdefghijk'
    result = get_youtube_video_duration_minutes(url)
    assert result == 3  # 125000 ms = 2.08 phút, làm tròn lên là 3

@mock.patch('courses.utils_youtube.requests.get')
def test_get_youtube_video_duration_minutes_no_duration(mock_get):
    mock_get.return_value.text = '{}'
    url = 'https://www.youtube.com/watch?v=abcdefghijk'
    result = get_youtube_video_duration_minutes(url)
    assert result is None

def test_get_youtube_video_duration_minutes_invalid_url():
    url = 'https://www.example.com/'
    result = get_youtube_video_duration_minutes(url)
    assert result is None

@mock.patch('courses.utils_youtube.requests.get', side_effect=Exception('Network error'))
def test_get_youtube_video_duration_minutes_exception(mock_get):
    url = 'https://www.youtube.com/watch?v=abcdefghijk'
    result = get_youtube_video_duration_minutes(url)
    assert result is None
