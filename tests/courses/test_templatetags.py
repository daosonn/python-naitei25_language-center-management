import pytest
from courses.templatetags import youtube, review_extras, quiz_tags, quiz_extras, course_media

# youtube.py
def test_extract_id():
    assert youtube._extract_id("https://youtu.be/abc123") == "abc123"
    assert youtube._extract_id("https://www.youtube.com/watch?v=xyz789") == "xyz789"
    assert youtube._extract_id("https://youtube.com/embed/def456") == "def456"
    assert youtube._extract_id("invalid") == "invalid"

def test_yt_embed():
    url = "https://youtu.be/abc123"
    embed = youtube.yt_embed(url)
    assert "youtube.com/embed/abc123" in embed

# review_extras.py
def test_star_percent():
    class Review:
        def __init__(self, star):
            self.star = star
    class Reviews:
        def __init__(self, items):
            self._items = items
        def count(self):
            return len(self._items)
        def __iter__(self):
            return iter(self._items)
        def __len__(self):
            return len(self._items)
    reviews = Reviews([Review(5), Review(4), Review(5)])
    assert review_extras.star_percent(reviews, 5) == 0
    assert review_extras.star_percent(reviews, 4) == 0
    assert review_extras.star_percent(Reviews([]), 5) == 0

# quiz_extras.py
def test_get_item():
    d = {"a": 1, "b": 2}
    assert quiz_extras.get_item(d, "a") == 1
    assert quiz_extras.get_item(d, "c") is None

# course_media.py
def test_course_cover_url_and_img():
    class Dummy:
        cover = None
        id = 1
    c = Dummy()
    url = course_media.course_cover_url(c)
    assert "placeholders" in url
    img = course_media.course_cover_img(c)
    assert isinstance(img, dict)
    assert "src" in img

# quiz_tags.py
def test_answer_state_and_icon():
    class Question:
        choices = [1]
    class Dummy:
        is_correct = True
        is_selected = True
        is_submitted = True
        state = "correct"
        question = Question()
        # for _answer_state logic
        def __getattr__(self, name):
            return True
    d = Dummy()
    d.is_correct = True
    d.is_selected = True
    d.is_submitted = True
    d.question = Question()
    assert quiz_tags._answer_state(d) in ("correct", "wrong", "incorrect", "unanswered")
    assert quiz_tags.answer_state(d) in ("correct", "incorrect", "unanswered", "skip", "wrong")
    assert "qi-correct" in quiz_tags.state_icon("correct")
    assert "qi-incorrect" in quiz_tags.state_icon("incorrect")
    assert "qi-unanswered" in quiz_tags.state_icon("unanswered")

def test_result_actions():
    class Course:
        id = 1
        slug = "slug"
    class Lesson:
        id = 2
        course = Course()
    class Quiz:
        lesson = Lesson()
    class Dummy:
        id = 1
        can_retry = True
        can_review = True
        quiz = Quiz()
    result = quiz_tags.result_actions(Dummy())
    assert isinstance(result, dict)
    assert "lesson_url" in result
    assert "retry_url" in result

def test_answer_badge_and_renderers():
    class Dummy:
        is_correct = True
        is_selected = True
        is_submitted = True
        text = "A"
        choices = ["A", "B"]
        question = object()
    d = Dummy()
    badge = quiz_tags.answer_badge(d)
    assert isinstance(badge, dict)
    assert "state" in badge
    # These return dicts for inclusion_tag
    assert isinstance(quiz_tags.render_answer_header(d, 1), dict)
    assert isinstance(quiz_tags.render_choice_list(d), dict)
    assert isinstance(quiz_tags.render_all_choices(d), dict)
