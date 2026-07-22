from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models


class AnalyticsService:
    @staticmethod
    def overview(db: Session) -> dict:
        now = datetime.now(timezone.utc)
        today = now.date()
        month_start = today.replace(day=1)
        week_start = today - timedelta(days=6)

        total_users = db.query(models.User).filter(models.User.role != "admin").count()
        success_revenue = (
            db.query(func.coalesce(func.sum(models.Payment.amount), 0))
            .filter(models.Payment.payment_status == "success")
            .scalar()
            or Decimal("0.00")
        )
        monthly_revenue = (
            db.query(func.coalesce(func.sum(models.Payment.amount), 0))
            .filter(models.Payment.payment_status == "success", func.date(models.Payment.paid_at) >= month_start)
            .scalar()
            or Decimal("0.00")
        )
        todays_revenue = (
            db.query(func.coalesce(func.sum(models.Payment.amount), 0))
            .filter(models.Payment.payment_status == "success", func.date(models.Payment.paid_at) == today)
            .scalar()
            or Decimal("0.00")
        )
        popular_course = (
            db.query(models.Course.title, func.count(models.Enrollment.id).label("enrollment_count"))
            .outerjoin(models.Enrollment, models.Enrollment.course_id == models.Course.id)
            .group_by(models.Course.id)
            .order_by(func.count(models.Enrollment.id).desc(), models.Course.title.asc())
            .first()
        )
        completion_avg = (
            db.query(func.coalesce(func.avg(models.Progress.progress_percent), 0)).scalar()
            or Decimal("0.00")
        )
        return {
            "total_users": total_users,
            "new_users_today": db.query(models.User).filter(models.User.role != "admin", func.date(models.User.date_joined) == today).count(),
            "new_users_this_month": db.query(models.User).filter(models.User.role != "admin", func.date(models.User.date_joined) >= month_start).count(),
            "active_users": db.query(models.User).filter(models.User.role != "admin", models.User.is_active.is_(True)).count(),
            "inactive_users": db.query(models.User).filter(models.User.role != "admin", models.User.is_active.is_(False)).count(),
            "student_count": db.query(models.User).filter(models.User.role == "student").count(),
            "instructor_count": db.query(models.User).filter(models.User.role == "instructor").count(),
            "total_courses": db.query(models.Course).count(),
            "published_courses": db.query(models.Course).filter(models.Course.status == "published").count(),
            "premium_courses": db.query(models.Course).filter(models.Course.is_premium.is_(True)).count(),
            "free_courses": db.query(models.Course).filter(models.Course.is_premium.is_(False)).count(),
            "active_subscriptions": db.query(models.Subscription).filter(models.Subscription.status == "active", models.Subscription.end_date >= now).count(),
            "expired_subscriptions": db.query(models.Subscription).filter(models.Subscription.status == "expired").count(),
            "renewed_subscriptions": db.query(models.Subscription).filter(models.Subscription.auto_renew.is_(True)).count(),
            "cancelled_subscriptions": db.query(models.Subscription).filter(models.Subscription.status == "cancelled").count(),
            "new_subscriptions": db.query(models.Subscription).filter(func.date(models.Subscription.created_at) >= month_start).count(),
            "todays_revenue": todays_revenue,
            "monthly_revenue": monthly_revenue,
            "total_revenue": success_revenue,
            "popular_course": popular_course.title if popular_course else None,
            "completion_rate": Decimal(completion_avg).quantize(Decimal("0.01")),
            "successful_payments": db.query(models.Payment).filter(models.Payment.payment_status == "success").count(),
            "failed_payments": db.query(models.Payment).filter(models.Payment.payment_status == "failed").count(),
            "activity_count": db.query(models.ActivityLog).count(),
            "daily_activity": db.query(models.ActivityLog).filter(func.date(models.ActivityLog.created_at) == today).count(),
            "weekly_activity": db.query(models.ActivityLog).filter(func.date(models.ActivityLog.created_at) >= week_start).count(),
            "unread_notifications": db.query(models.Notification).filter(models.Notification.is_read.is_(False)).count(),
        }

    @staticmethod
    def monthly_revenue(db: Session) -> list[dict]:
        rows = (
            db.query(
                func.date_trunc("month", models.Payment.paid_at).label("month"),
                func.coalesce(func.sum(models.Payment.amount), 0).label("revenue"),
            )
            .filter(models.Payment.payment_status == "success")
            .group_by("month")
            .order_by("month")
            .all()
        )
        return [{"month": row.month.date(), "revenue": row.revenue} for row in rows if row.month]

    @staticmethod
    def revenue_by_plan(db: Session) -> list[dict]:
        rows = (
            db.query(models.Plan.name, func.coalesce(func.sum(models.Payment.amount), 0).label("revenue"))
            .join(models.Subscription, models.Subscription.plan_id == models.Plan.id)
            .join(models.Payment, models.Payment.subscription_id == models.Subscription.id)
            .filter(models.Payment.payment_status == "success")
            .group_by(models.Plan.name)
            .order_by(func.sum(models.Payment.amount).desc())
            .all()
        )
        return [{"plan": row.name, "revenue": row.revenue} for row in rows]


def analytics_overview(db: Session) -> dict:
    return AnalyticsService.overview(db)


def monthly_revenue(db: Session) -> list[dict]:
    return AnalyticsService.monthly_revenue(db)
