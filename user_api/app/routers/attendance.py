from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services import notification_service

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def _instructor_course(db: Session, course_id: int, user: models.User) -> models.Course:
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if user.role != "admin" and course.instructor_id != user.id:
        raise HTTPException(status_code=403, detail="You can only manage your own courses")
    return course


@router.post("/mark", response_model=list[schemas.AttendanceOut], status_code=status.HTTP_201_CREATED)
def mark_attendance(
    payload: schemas.AttendanceMarkRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_instructor),
):
    _instructor_course(db, payload.course_id, current_user)
    student_ids = [record.student_id for record in payload.records]
    if len(student_ids) != len(set(student_ids)):
        raise HTTPException(status_code=409, detail="A student appears more than once in this request")

    enrolled = {
        row.user_id for row in db.query(models.Enrollment).filter(
            models.Enrollment.course_id == payload.course_id,
            models.Enrollment.user_id.in_(student_ids),
        ).all()
    }
    missing = sorted(set(student_ids) - enrolled)
    if missing:
        raise HTTPException(status_code=422, detail=f"Students are not enrolled in this course: {missing}")

    duplicates = db.query(models.Attendance.student_id).filter(
        models.Attendance.course_id == payload.course_id,
        models.Attendance.date == payload.date,
        models.Attendance.student_id.in_(student_ids),
    ).all()
    if duplicates:
        raise HTTPException(status_code=409, detail="Attendance already exists for one or more students on this date")

    rows = [models.Attendance(
        student_id=record.student_id,
        course_id=payload.course_id,
        date=payload.date,
        status=record.status,
        marked_by=current_user.id,
    ) for record in payload.records]
    db.add_all(rows)
    try:
        db.flush()
        for row in rows:
            notification_service.create_notification(
                db=db,
                user_id=row.student_id,
                title="Attendance marked",
                message=f"Your attendance for course #{payload.course_id} on {payload.date} is {row.status}.",
                notification_type="attendance_marked",
                link="/student/attendance/",
            )
        notification_service.NotificationService.notify_admins(
            db=db,
            title="Attendance Recorded",
            message=f"{current_user.name} marked {len(rows)} attendance record(s) for course #{payload.course_id}.",
            notification_type="attendance_marked",
            link="/analytics/",
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate attendance entry")
    return rows


@router.get("/student/{student_id}/", response_model=schemas.AttendanceSummary)
def student_attendance(
    student_id: int,
    course_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Students can only view their own attendance")
    if current_user.role in ("admin", "instructor"):
        _instructor_course(db, course_id, current_user)
    records = db.query(models.Attendance).filter(
        models.Attendance.student_id == student_id,
        models.Attendance.course_id == course_id,
    ).order_by(models.Attendance.date.desc()).all()
    present = sum(row.status == "Present" for row in records)
    late = sum(row.status == "Late" for row in records)
    total = len(records)
    percentage = Decimal(present * 100 / total).quantize(Decimal("0.01")) if total else Decimal("0.00")
    absent = sum(row.status == "Absent" for row in records)
    return {"total": total, "present": present, "absent": absent, "late": late, "percentage": percentage, "records": records}


@router.get("/course/{course_id}/", response_model=list[schemas.AttendanceOut])
def course_attendance(
    course_id: int,
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_instructor),
):
    _instructor_course(db, course_id, current_user)
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=422, detail="from date must not be after to date")
    query = db.query(models.Attendance).filter(models.Attendance.course_id == course_id)
    if from_date:
        query = query.filter(models.Attendance.date >= from_date)
    if to_date:
        query = query.filter(models.Attendance.date <= to_date)
    return query.order_by(models.Attendance.date.desc(), models.Attendance.student_id).all()
