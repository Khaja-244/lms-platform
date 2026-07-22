"""
app/routers/courses.py

Course Management APIs
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from .. import auth, models, schemas
from ..database import get_db
from ..services import activity_service, notification_service
from ..services.subscription_service import has_active_subscription

router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


# ==========================================================
# List Courses
# ==========================================================

@router.get("/", response_model=list[schemas.CourseOut])
def list_courses(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role == "instructor":
        return db.query(models.Course).filter(
            models.Course.instructor_id == current_user.id,
        ).order_by(models.Course.created_at.desc()).all()
    if current_user.role == "admin":
        return db.query(models.Course).order_by(models.Course.created_at.desc()).all()

    subscribed = has_active_subscription(
        db,
        current_user.id,
    )

    query = db.query(models.Course).filter(
        models.Course.status == "published"
    )

    if not subscribed:
        query = query.filter(
            models.Course.is_premium.is_(False)
        )

    return query.order_by(
        models.Course.created_at.desc()
    ).all()


@router.get("/{course_id}/students/", response_model=list[schemas.UserOut])
def course_students(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_instructor),
):
    _get_owned_course(course_id, current_user, db)
    return (
        db.query(models.User)
        .join(models.Enrollment, models.Enrollment.user_id == models.User.id)
        .filter(
            models.Enrollment.course_id == course_id,
            models.User.role == "student",
            models.User.is_active.is_(True),
        )
        .order_by(models.User.name)
        .all()
    )


# ==========================================================
# Course Details
# ==========================================================

@router.get("/{course_id}", response_model=schemas.CourseDetailOut)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    course = (
        db.query(models.Course)
        .options(
            joinedload(models.Course.lessons)
        )
        .filter(
            models.Course.id == course_id
        )
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    if current_user.role == "student" and course.status != "published":
        raise HTTPException(status_code=404, detail="Course not found")
    if current_user.role == "instructor" and course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own unpublished course content")

    if course.is_premium and current_user.role == "student" and not has_active_subscription(db, current_user.id):
        raise HTTPException(
            status_code=403,
            detail="An active subscription is required to access this premium course",
        )

    return course


# ==========================================================
# Create Course
# ==========================================================

@router.post(
    "/",
    response_model=schemas.CourseOut,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    payload: schemas.CourseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_instructor),
):
    course = models.Course(
        title=payload.title,
        description=payload.description,
        thumbnail=payload.thumbnail,
        duration=payload.duration,
        level=payload.level,
        instructor_id=current_user.id,
        status=payload.status,
        is_premium=payload.is_premium,
        price=payload.price,
        instructor_commission=payload.instructor_commission,
    )

    db.add(course)
    db.flush()
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="course_created",
        action_detail=f"Created course {course.id}: {course.title}",
        ip_address=activity_service.get_client_ip(request),
    )
    db.commit()
    db.refresh(course)

    return course


# ==========================================================
# Helper
# ==========================================================

def _get_owned_course(
    course_id: int,
    current_user: models.User,
    db: Session,
) -> models.Course:

    course = (
        db.query(models.Course)
        .filter(
            models.Course.id == course_id
        )
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    if course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can manage only your own courses.",
        )

    return course


# ==========================================================
# Update Course
# ==========================================================

@router.put(
    "/{course_id}",
    response_model=schemas.CourseOut,
)
def update_course(
    course_id: int,
    payload: schemas.CourseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_instructor),
):
    course = _get_owned_course(
        course_id,
        current_user,
        db,
    )

    updates = payload.model_dump(
        exclude_unset=True
    )

    for field, value in updates.items():
        setattr(course, field, value)

    course.updated_at = datetime.now(
        timezone.utc
    )

    if updates:
        notification_service.notify_course_enrollees(
            db=db,
            course_id=course.id,
            message=f"The course '{course.title}' has been updated.",
            title="Course Updated",
            notification_type="course_update",
        )
        activity_service.log_activity(
            db=db,
            user_id=current_user.id,
            action_type="course_updated",
            action_detail=f"Updated course {course.id}: {course.title}",
            ip_address=activity_service.get_client_ip(request),
        )

    db.commit()
    db.refresh(course)

    return course


# ==========================================================
# Delete Course
# ==========================================================

@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_course(
    course_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_instructor),
):
    course = _get_owned_course(
        course_id,
        current_user,
        db,
    )

    db.delete(course)
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="course_deleted",
        action_detail=f"Deleted course {course.id}: {course.title}",
        ip_address=activity_service.get_client_ip(request),
    )
    db.commit()

    return None


# ==========================================================
# Add Lesson
# ==========================================================

@router.post(
    "/{course_id}/lessons/",
    response_model=schemas.LessonOut,
    status_code=status.HTTP_201_CREATED,
)
def add_lesson(
    course_id: int,
    payload: schemas.LessonCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_instructor),
):
    course = _get_owned_course(
        course_id,
        current_user,
        db,
    )

    lesson = models.Lesson(
        course_id=course.id,
        **payload.model_dump(),
    )

    db.add(lesson)
    notification_service.notify_course_enrollees(
        db=db,
        course_id=course.id,
        message=f"A new lesson was added to '{course.title}': {lesson.title}.",
        title="New Lesson Published",
        notification_type="new_lesson_published",
    )
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="lesson_created",
        action_detail=f"Added lesson to course {course.id}: {lesson.title}",
        ip_address=activity_service.get_client_ip(request),
    )
    db.commit()
    db.refresh(lesson)

    return lesson
