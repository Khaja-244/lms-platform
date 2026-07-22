"""
app/routers/enrollment.py

Endpoints:
    POST /enroll/       - Enroll in a course
    GET  /my-courses/   - View enrolled courses
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services import activity_service, notification_service
from ..services.subscription_service import has_active_subscription

router = APIRouter(tags=["Enrollment"])


# ==========================================================
# Enroll in Course
# ==========================================================
@router.post(
    "/enroll/",
    response_model=schemas.EnrollmentOut,
    status_code=status.HTTP_201_CREATED,
)
def enroll_in_course(
    payload: schemas.EnrollRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can enroll in courses")
    # Check course exists
    course = (
        db.query(models.Course)
        .filter(models.Course.id == payload.course_id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    # Only published courses can be enrolled
    if course.status != "published":
        raise HTTPException(
            status_code=400,
            detail="This course is not open for enrollment",
        )

    if course.is_premium and not has_active_subscription(db, current_user.id):
        raise HTTPException(
            status_code=403,
            detail="An active subscription is required to enroll in this premium course",
        )

    # Prevent duplicate enrollment
    existing = (
        db.query(models.Enrollment)
        .filter(
            models.Enrollment.user_id == current_user.id,
            models.Enrollment.course_id == course.id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You are already enrolled in this course",
        )

    # Create enrollment
    enrollment = models.Enrollment(
        user_id=current_user.id,
        course_id=course.id,

        # Required because Django table has NOT NULL
        enrolled_on=datetime.now(timezone.utc),
    )

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    # Create initial progress
    progress = models.Progress(
        enrollment_id=enrollment.id,
        completed_lessons=0,
        progress_percent=0,
    )

    db.add(progress)
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="course_enrolled",
        action_detail=f"Enrolled in course {course.id}: {course.title}",
        ip_address=activity_service.get_client_ip(request),
    )
    notification_service.create_notification(
        db=db,
        user_id=current_user.id,
        title="Course Enrolled",
        message=f"You are enrolled in '{course.title}'.",
        notification_type="course_enrolled",
        link=f"/student/course/{course.id}/",
    )
    db.commit()

    return enrollment


# ==========================================================
# My Courses
# ==========================================================
@router.get(
    "/my-courses/",
    response_model=list[schemas.CourseOut],
)
def my_courses(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    enrollments = (
        db.query(models.Enrollment)
        .filter(models.Enrollment.user_id == current_user.id)
        .all()
    )

    return [enrollment.course for enrollment in enrollments]


@router.get("/enrollments/me", response_model=list[schemas.EnrollmentOut])
def my_enrollments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student role required")
    return db.query(models.Enrollment).filter(
        models.Enrollment.user_id == current_user.id
    ).order_by(models.Enrollment.enrolled_on.desc()).all()
