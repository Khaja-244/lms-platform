from sqlalchemy.orm import Session

from .. import models
from . import email_service


class NotificationService:
    DEFAULT_ICONS = {
        "welcome_registration": "bi-person-check",
        "payment_success": "bi-credit-card-2-front",
        "payment_failed": "bi-exclamation-octagon",
        "subscription_activated": "bi-patch-check",
        "subscription_renewed": "bi-arrow-repeat",
        "subscription_expiring": "bi-hourglass-split",
        "subscription_expired": "bi-calendar-x",
        "course_purchased": "bi-bag-check",
        "course_enrolled": "bi-journal-check",
        "course_update": "bi-megaphone",
        "new_lesson_published": "bi-play-circle",
        "password_changed": "bi-shield-lock",
        "instructor_message": "bi-chat-dots",
        "admin_broadcast": "bi-broadcast",
        "system": "bi-bell",
        "login": "bi-box-arrow-in-right",
        "new_registration": "bi-person-plus",
        "subscription_requested": "bi-cart-check",
        "chat_message": "bi-chat-left-text",
        "attendance_marked": "bi-calendar-check",
        "assignment_created": "bi-file-earmark-plus",
        "assignment_submitted": "bi-file-earmark-check",
        "assignment_graded": "bi-award",
    }

    @classmethod
    def create_notification(
        cls,
        db: Session,
        user_id: int,
        message: str,
        notification_type: str = "system",
        title: str | None = None,
        link: str = "",
        email_sent: bool = False,
    ) -> models.Notification:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        resolved_title = title or email_service.notification_subject(notification_type)
        if user is not None:
            email_sent = email_service.send_email(
                to_email=user.email,
                subject=resolved_title,
                body=f"Hello {user.name},\n\n{message}\n\nRegards,\nSubscription-Based Video Learning Platform",
            )

        notification = models.Notification(
            user_id=user_id,
            title=resolved_title,
            message=message,
            notification_type=notification_type,
            icon=cls.DEFAULT_ICONS.get(notification_type, "bi-bell"),
            link=link,
            email_sent=email_sent,
        )
        db.add(notification)
        db.flush()
        return notification

    @classmethod
    def broadcast(cls, db: Session, title: str, message: str, link: str = "") -> int:
        users = db.query(models.User).filter(models.User.is_active.is_(True), models.User.role != "admin").all()
        for user in users:
            cls.create_notification(
                db=db,
                user_id=user.id,
                title=title,
                message=message,
                notification_type="admin_broadcast",
                link=link,
            )
        return len(users)

    @classmethod
    def notify_admins(
        cls,
        db: Session,
        title: str,
        message: str,
        notification_type: str = "system",
        link: str = "/analytics/notifications/",
    ) -> int:
        admins = db.query(models.User).filter(
            models.User.role == "admin",
            models.User.is_active.is_(True),
        ).all()
        for admin in admins:
            cls.create_notification(
                db=db,
                user_id=admin.id,
                title=title,
                message=message,
                notification_type=notification_type,
                link=link,
            )
        return len(admins)


def create_notification(
    db: Session,
    user_id: int,
    message: str,
    notification_type: str = "system",
    title: str | None = None,
    link: str = "",
    email_sent: bool = False,
) -> models.Notification:
    return NotificationService.create_notification(
        db=db,
        user_id=user_id,
        message=message,
        notification_type=notification_type,
        title=title,
        link=link,
        email_sent=email_sent,
    )


def notify_course_enrollees(
    db: Session,
    course_id: int,
    message: str,
    title: str = "Course Updated",
    notification_type: str = "course_update",
) -> None:
    enrollments = db.query(models.Enrollment).filter(models.Enrollment.course_id == course_id).all()
    for enrollment in enrollments:
        create_notification(
            db=db,
            user_id=enrollment.user_id,
            message=message,
            notification_type=notification_type,
            title=title,
            link=f"/courses/{course_id}",
        )
