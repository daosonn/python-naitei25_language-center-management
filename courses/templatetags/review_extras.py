from django import template

register = template.Library()

def star_percent(reviews, star):
    try:
        star = int(star)
    except Exception:
        return 0
    total = reviews.count() if hasattr(reviews, 'count') else len(reviews)
    if not total:
        return 0
    count = 0
    for r in reviews:
        if hasattr(r, 'rating') and int(r.rating) == star:
            count += 1
    return int(round(count * 100 / total))

register.filter('star_percent', star_percent)
