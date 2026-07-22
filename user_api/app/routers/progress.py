"""
app/routers/progress.py

Endpoints:
    POST /progress/update/ - Update progress
    GET  /progress/view/   - View progress status
"""

from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services import activity_service, notification_service

router = APIRouter(prefix="/progress", tags=["Progress"])


def _recalculate_percent(enrollment: models.Enrollment, completed_lessons: int) -> Decimal:
    total_lessons = len(enrollment.course.lessons)
    if total_lessons == 0:
        return Decimal("0.00")
    percent = (Decimal(completed_lessons) / Decimal(total_lessons)) * Decimal(100)
    return percent.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@router.post("/update/", response_model=schemas.ProgressOut)
def update_progress(
    payload: schemas.ProgressUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    enrollment = (
        db.query(models.Enrollment).filter(models.Enrollment.id == payload.enrollment_id).first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    if enrollment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own progress")

    total_lessons = len(enrollment.course.lessons)
    if payload.completed_lessons > total_lessons:
        raise HTTPException(
            status_code=400,
            detail=f"completed_lessons cannot exceed the course's total lessons ({total_lessons})",
        )

    progress = enrollment.progress
    if progress is None:
        progress = models.Progress(enrollment_id=enrollment.id)
        db.add(progress)

    progress.completed_lessons = payload.completed_lessons
    progress.progress_percent = _recalculate_percent(enrollment, payload.completed_lessons)
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="lesson_completion" if progress.progress_percent == Decimal("100.00") else "progress_updated",
        action_detail=f"Updated progress for enrollment {enrollment.id} to {progress.progress_percent}%",
        ip_address=activity_service.get_client_ip(request),
    )
    if progress.progress_percent == Decimal("100.00"):
        notification_service.create_notification(
            db=db,
            user_id=current_user.id,
            title="Lesson Completion",
            message=f"You completed '{enrollment.course.title}'.",
            notification_type="new_lesson_published",
            link=f"/courses/{enrollment.course_id}",
        )

    db.commit()
    db.refresh(progress)
    return progress


@router.get("/view/", response_model=list[schemas.ProgressOut])
def view_progress(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Returns progress for every course the current user is enrolled in."""
    enrollments = (
        db.query(models.Enrollment).filter(models.Enrollment.user_id == current_user.id).all()
    )
    return [e.progress for e in enrollments if e.progress is not None]
