from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from .. import auth, models, schemas
from ..database import get_db
from ..services import notification_service

router = APIRouter(prefix="/assignments", tags=["Assignments"])
UPLOAD_DIR = Path("uploads/assignments")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".zip", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024


async def _save_upload(file: UploadFile) -> tuple[str, str]:
    original = Path(file.filename or "upload").name
    extension = Path(original).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Unsupported file type")
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB limit")
    safe_name = f"{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / safe_name
    destination.write_bytes(content)
    return f"/uploads/assignments/{safe_name}", original


def _owned_course(db: Session, course_id: int, user: models.User) -> models.Course:
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if user.role != "admin" and course.instructor_id != user.id:
        raise HTTPException(status_code=403, detail="You can only manage your own courses")
    return course


@router.post("/create", response_model=schemas.AssignmentOut, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    course_id: int = Form(...), title: str = Form(...), description: str = Form(""),
    deadline: datetime = Form(...), file: UploadFile | None = File(None),
    db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_instructor),
):
    _owned_course(db, course_id, current_user)
    deadline = deadline if deadline.tzinfo else deadline.replace(tzinfo=timezone.utc)
    if deadline <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Deadline must be in the future")
    file_url = ""
    if file:
        file_url, _ = await _save_upload(file)
    assignment = models.Assignment(course_id=course_id, title=title.strip(), description=description.strip(),
                                   deadline=deadline, file_url=file_url, created_by=current_user.id)
    if not assignment.title:
        raise HTTPException(status_code=422, detail="Title is required")
    db.add(assignment)
    db.flush()
    student_ids = [row.user_id for row in db.query(models.Enrollment).filter(models.Enrollment.course_id == course_id)]
    for user_id in student_ids:
        notification_service.create_notification(
            db=db,
            user_id=user_id,
            title="New Assignment",
            message=f"{assignment.title} is due on {assignment.deadline.date()}.",
            notification_type="assignment_created",
            link="/student/assignments/",
        )
    notification_service.NotificationService.notify_admins(
        db=db,
        title="Assignment Created",
        message=f"{current_user.name} created '{assignment.title}' for course #{course_id}.",
        notification_type="assignment_created",
        link="/analytics/",
    )
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/", response_model=list[schemas.AssignmentOut])
def list_assignments(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    query = db.query(models.Assignment).options(joinedload(models.Assignment.course))
    if current_user.role == "student":
        course_ids = db.query(models.Enrollment.course_id).filter(models.Enrollment.user_id == current_user.id)
        query = query.filter(models.Assignment.course_id.in_(course_ids))
    elif current_user.role == "instructor":
        query = query.join(models.Course).filter(models.Course.instructor_id == current_user.id)
    return query.order_by(models.Assignment.deadline.asc()).all()


@router.post("/submit", response_model=schemas.SubmissionOut, status_code=status.HTTP_201_CREATED)
async def submit_assignment(
    assignment_id: int = Form(...), student_id: int | None = Form(None), file: UploadFile = File(...),
    db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student role required")
    if student_id is not None and student_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot submit for another student")
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    deadline = assignment.deadline if assignment.deadline.tzinfo else assignment.deadline.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > deadline:
        raise HTTPException(status_code=409, detail="The submission deadline has passed")
    enrolled = db.query(models.Enrollment).filter_by(user_id=current_user.id, course_id=assignment.course_id).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")
    if db.query(models.Submission).filter_by(assignment_id=assignment_id, student_id=current_user.id).first():
        raise HTTPException(status_code=409, detail="You have already submitted this assignment")
    file_url, original = await _save_upload(file)
    submission = models.Submission(assignment_id=assignment_id, student_id=current_user.id,
                                   file_url=file_url, original_filename=original)
    db.add(submission)
    course = db.query(models.Course).filter(models.Course.id == assignment.course_id).first()
    notification_service.create_notification(
        db=db,
        user_id=course.instructor_id,
        title="Assignment Submitted",
        message=f"{current_user.name} submitted '{assignment.title}'.",
        notification_type="assignment_submitted",
        link="/instructor/dashboard/#assignments",
    )
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/submissions/", response_model=list[schemas.SubmissionOut])
def list_submissions(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    query = db.query(models.Submission).join(models.Assignment).join(models.Course)
    if current_user.role == "student":
        query = query.filter(models.Submission.student_id == current_user.id)
    elif current_user.role == "instructor":
        query = query.filter(models.Course.instructor_id == current_user.id)
    return query.order_by(models.Submission.submitted_at.desc()).all()


@router.put("/grade", response_model=schemas.SubmissionOut)
def grade_submission(
    payload: schemas.GradeSubmissionRequest, db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_instructor),
):
    submission = db.query(models.Submission).options(joinedload(models.Submission.assignment)).filter(
        models.Submission.id == payload.submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    _owned_course(db, submission.assignment.course_id, current_user)
    submission.grade, submission.remarks = payload.grade, payload.remarks.strip()
    submission.graded_at, submission.graded_by = datetime.now(timezone.utc), current_user.id
    notification_service.create_notification(
        db=db,
        user_id=submission.student_id,
        title="Assignment Graded",
        message=f"Your submission received {payload.grade}/100.",
        notification_type="assignment_graded",
        link="/student/assignments/",
    )
    notification_service.NotificationService.notify_admins(
        db=db,
        title="Assignment Graded",
        message=f"{current_user.name} graded submission #{submission.id}: {payload.grade}/100.",
        notification_type="assignment_graded",
        link="/analytics/",
    )
    db.commit()
    db.refresh(submission)
    return submission
