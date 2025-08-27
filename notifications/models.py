from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
	message = models.TextField()
	created_at = models.DateTimeField(default=timezone.now)
	is_read = models.BooleanField(default=False)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.user}: {self.message[:40]}{'...' if len(self.message) > 40 else ''}"
    