from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .services import ActivityLogService


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ActivityLogService.log(user, "login", "User logged in to Django admin panel.", request)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    ActivityLogService.log(user, "logout", "User logged out from Django admin panel.", request)
