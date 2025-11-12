from typing import Optional
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse

from .models import AppUser

SESSION_KEY_ID = 'custom_user_id'


def get_current_user(request: HttpRequest) -> Optional[AppUser]:
    uid = request.session.get(SESSION_KEY_ID)
    if not uid:
        return None
    try:
        return AppUser.objects.using('historical').get(id=uid)
    except AppUser.DoesNotExist:
        return None


def login_user(request: HttpRequest, user: AppUser):
    request.session[SESSION_KEY_ID] = user.id


def logout_user(request: HttpRequest):
    request.session.pop(SESSION_KEY_ID, None)


class CustomLoginRequiredMixin:
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if not get_current_user(request):
            next_url = request.get_full_path()
            return HttpResponseRedirect(f"{reverse('custom-login')}?next={next_url}")
        return super().dispatch(request, *args, **kwargs)

