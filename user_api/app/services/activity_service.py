from sqlalchemy.orm import Session

from .. import models


def get_client_ip(request) -> str | None:
    if request is None:
        return None
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


class ActivityLogService:
    @staticmethod
    def log_activity(
        db: Session,
        user_id: int,
        action_type: str,
        action_detail: str = "",
        ip_address: str | None = None,
    ) -> models.ActivityLog:
        activity = models.ActivityLog(
            user_id=user_id,
            action_type=action_type,
            action_detail=action_detail,
            ip_address=ip_address,
        )
        db.add(activity)
        db.flush()
        return activity


def log_activity(
    db: Session,
    user_id: int,
    action_type: str,
    action_detail: str = "",
    ip_address: str | None = None,
) -> models.ActivityLog:
    return ActivityLogService.log_activity(
        db=db,
        user_id=user_id,
        action_type=action_type,
        action_detail=action_detail,
        ip_address=ip_address,
    )
