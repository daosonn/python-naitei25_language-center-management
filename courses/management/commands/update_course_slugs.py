from django.core.management.base import BaseCommand
from courses.models import Course
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Tự động cập nhật slug cho các Course chưa có slug.'

    def handle(self, *args, **options):
        updated = 0
        for course in Course.objects.all():
            if not course.slug:
                base_slug = slugify(course.name)
                slug = base_slug
                i = 1
                # Đảm bảo slug là duy nhất
                while Course.objects.filter(slug=slug).exclude(pk=course.pk).exists():
                    slug = f"{base_slug}-{i}"
                    i += 1
                course.slug = slug
                course.save()
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"Đã cập nhật slug cho: {course.name} -> {slug}"))
        if updated == 0:
            self.stdout.write(self.style.WARNING("Không có Course nào cần cập nhật slug."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Đã cập nhật slug cho {updated} Course."))
