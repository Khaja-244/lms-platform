from .models import Notification


def notification_summary(request):
    if not request.user.is_authenticated:
        return {}
    if getattr(request.user, "role", "") == "admin":
        base_query = Notification.objects.all()
    else:
        base_query = Notification.objects.filter(user=request.user)
    notifications = base_query.order_by("-created_at")[:5]
    return {
        "nav_notifications": notifications,
        "nav_unread_notification_count": base_query.filter(is_read=False).count(),
    }
