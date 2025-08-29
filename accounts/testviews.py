from django.http import HttpResponse
from accounts.permissions import user_role_required, admin_required, staff_required, active_user_required

def dummy_view(request):
    return HttpResponse("ok")

user_role_view = user_role_required(["student"])(dummy_view)
admin_view = admin_required(dummy_view)
staff_view = staff_required(dummy_view)
active_user_view = active_user_required(dummy_view)
