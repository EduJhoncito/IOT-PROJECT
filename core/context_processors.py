from .auth import get_current_user


def custom_user(request):
    return { 'custom_user': get_current_user(request) }

