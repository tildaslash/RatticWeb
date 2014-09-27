from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test


def rattic_staff_required(view_func):
    return user_passes_test(
        lambda u: u.is_active and u.is_staff,
        login_url=settings.LOGIN_URL,
        redirect_field_name=REDIRECT_FIELD_NAME
    )(view_func)
