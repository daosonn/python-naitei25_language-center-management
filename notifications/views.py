from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def unread_notifications(request):
	qs = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
	data = [
		{
			'id': n.id,
			'message': n.message,
			'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
		}
		for n in qs
	]
	return JsonResponse({'count': qs.count(), 'notifications': data})
