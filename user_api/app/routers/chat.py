import json
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app import models, schemas
from app.services.chat_service import chat_service
from app.services.redis_service import redis_service

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

UPLOAD_DIR = Path("uploads/chat")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _publish_message(payload: dict) -> None:
    wire_payload = dict(payload)
    wire_payload["event"] = "message"
    for field in ("created_at", "delivered_at", "read_at"):
        value = wire_payload.get(field)
        if value is not None:
            wire_payload[field] = value.isoformat()
    redis_service.publish("lms_chat", json.dumps(wire_payload))


@router.get("/contacts", response_model=list[schemas.UserInfo])
def chat_contacts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.User).filter(
        models.User.id != current_user.id,
        models.User.is_active.is_(True),
    )
    if current_user.role == "student":
        query = query.filter(models.User.role == "instructor")
    elif current_user.role == "instructor":
        student_ids = (
            db.query(models.Enrollment.user_id)
            .join(models.Course, models.Course.id == models.Enrollment.course_id)
            .filter(models.Course.instructor_id == current_user.id)
        )
        query = query.filter(
            models.User.id.in_(student_ids),
            models.User.role == "student",
        )
    else:
        query = query.filter(models.User.role.in_(["student", "instructor"]))
    return query.order_by(models.User.name).all()


# ==========================================================
# Create Room
# ==========================================================

@router.post(
    "/rooms",
    response_model=schemas.ChatRoomSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_room(
    request: schemas.ChatRoomCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    participant_ids = set(request.participant_ids) - {current_user.id}
    if request.room_type == "private" and len(participant_ids) != 1:
        raise HTTPException(status_code=422, detail="A private room requires exactly one other participant")
    valid_users = db.query(models.User.id).filter(models.User.id.in_(participant_ids), models.User.is_active.is_(True)).count()
    if valid_users != len(participant_ids):
        raise HTTPException(status_code=422, detail="One or more participants do not exist or are inactive")
    if request.room_type == "private":
        expected = participant_ids | {current_user.id}
        matching_rooms = []
        for existing_room in chat_service.get_user_rooms(db, current_user.id):
            if existing_room.room_type != "private":
                continue
            existing_ids = {
                row.user_id for row in db.query(models.ChatParticipant).filter(
                    models.ChatParticipant.room_id == existing_room.id
                ).all()
            }
            if existing_ids == expected:
                matching_rooms.append(existing_room)
        if matching_rooms:
            summaries = [
                chat_service.room_summary(db, existing_room, current_user.id)
                for existing_room in matching_rooms
            ]
            return max(
                summaries,
                key=lambda room: room["last_message_at"] or room["created_at"],
            )
    try:
        room = chat_service.create_room(
            db=db,
            creator_id=current_user.id,
            room_type=request.room_type,
            participant_ids=list(participant_ids),
            name=request.name,
        )
    except Exception:
        db.rollback()
        raise

    return chat_service.room_summary(db, room, current_user.id)


# ==========================================================
# My Rooms
# ==========================================================

@router.get(
    "/rooms",
    response_model=list[schemas.ChatRoomSummary],
)
def my_rooms(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    rooms = chat_service.get_user_rooms(db, current_user.id)
    summaries = [chat_service.room_summary(db, room, current_user.id) for room in rooms]
    summaries = sorted(
        summaries,
        key=lambda room: room["last_message_at"] or room["created_at"],
        reverse=True,
    )
    unique = []
    seen_private_participants = set()
    for room in summaries:
        if room["room_type"] == "private":
            key = tuple(sorted(
                participant["id"] for participant in room["participants"]
                if participant["id"] != current_user.id
            ))
            if key in seen_private_participants:
                continue
            seen_private_participants.add(key)
        unique.append(room)
    return unique


# ==========================================================
# Room Details
# ==========================================================

@router.get(
    "/rooms/{room_id}",
    response_model=schemas.ChatRoomSummary,
)
def room_details(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    room = chat_service.get_room(
        db=db,
        room_id=room_id,
    )

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )

    if not chat_service.is_room_participant(
        db=db,
        room_id=room_id,
        user_id=current_user.id,
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied.",
        )

    return chat_service.room_summary(db, room, current_user.id)
    
# ==========================================================
# Room Messages
# ==========================================================
@router.get(
    "/rooms/{room_id}/messages",
    response_model=schemas.ChatMessagePage,
)
def room_messages(
    room_id: int,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    room = chat_service.get_room(
        db=db,
        room_id=room_id,
    )

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )

    try:

        messages, total = chat_service.get_messages_paginated(
            db=db,
            room_id=room_id,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
        )

        total_pages = (
            (total + page_size - 1)
            // page_size
            if total > 0
            else 0
        )

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "messages": [
                chat_service.message_payload(db, message, current_user.id)
                for message in messages
            ],
        }

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e),
        )


# ==========================================================
# Send Text Message
# ==========================================================

@router.post(
    "/messages",
    response_model=schemas.ChatMessageOut,
)
def send_message(
    request: schemas.ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        saved = chat_service.send_message(
            db=db,
            room_id=request.room_id,
            sender_id=current_user.id,
            message=request.message,
            message_type=request.message_type,
        )
        payload = chat_service.message_payload(db, saved, current_user.id)
        _publish_message(payload)
        return payload

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
# ==========================================================
# Upload File
# ==========================================================

@router.post(
    "/upload/{room_id}",
    response_model=schemas.ChatMessageOut,
)
async def upload_file(
    room_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    room = chat_service.get_room(db, room_id)

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )

    if not chat_service.is_room_participant(
        db=db,
        room_id=room_id,
        user_id=current_user.id,
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied.",
        )

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        ".txt",
        ".zip",
    }

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10 MB.",
        )

    filename = f"{uuid4().hex}{extension}"

    destination = UPLOAD_DIR / filename

    with open(destination, "wb") as buffer:
        buffer.write(content)

    saved = chat_service.upload_file(
        db=db,
        room_id=room_id,
        sender_id=current_user.id,
        file_name=file.filename or filename,
        file_url=f"/uploads/chat/{filename}",
    )
    payload = chat_service.message_payload(db, saved, current_user.id)
    _publish_message(payload)
    return payload


@router.post(
    "/rooms/{room_id}/read",
    response_model=schemas.ChatReadResponse,
)
def mark_room_read(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not chat_service.is_room_participant(db, room_id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    message_ids = chat_service.mark_room_read(db, room_id, current_user.id)
    if message_ids:
        redis_service.publish(
            "lms_chat",
            json.dumps({
                "event": "read",
                "room_id": room_id,
                "user_id": current_user.id,
                "message_ids": message_ids,
            }),
        )
    return {"room_id": room_id, "read_count": len(message_ids)}


# ==========================================================
# Delete Message
# ==========================================================

@router.delete(
    "/messages/{message_id}",
)
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    success = chat_service.delete_message(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

    return {
        "success": True,
        "message": "Message deleted successfully",
    }


# ==========================================================
# Add Participant
# ==========================================================

@router.post(
    "/rooms/{room_id}/participants/{user_id}",
)
def add_participant(
    room_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    room = chat_service.get_room(
        db=db,
        room_id=room_id,
    )

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )
        return chat_service.message_payload(db, saved, current_user.id)

    if current_user.role != "admin" and room.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the room owner can manage participants")

    if not db.query(models.User).filter(models.User.id == user_id, models.User.is_active.is_(True)).first():
        raise HTTPException(status_code=404, detail="Active user not found")

    existing = (
        db.query(models.ChatParticipant)
        .filter(
            models.ChatParticipant.room_id == room_id,
            models.ChatParticipant.user_id == user_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="User already exists in room",
        )

    chat_service.add_participant(
        db=db,
        room_id=room_id,
        user_id=user_id,
    )

    return {
        "success": True,
        "message": "Participant added",
    }


# ==========================================================
# Remove Participant
# ==========================================================

@router.delete(
    "/rooms/{room_id}/participants/{user_id}",
)
def remove_participant(
    room_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    room = chat_service.get_room(db=db, room_id=room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    if current_user.role != "admin" and room.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the room owner can manage participants")
    if user_id == room.created_by:
        raise HTTPException(status_code=409, detail="The room owner cannot be removed")

    participant = (
        db.query(models.ChatParticipant)
        .filter(
            models.ChatParticipant.room_id == room_id,
            models.ChatParticipant.user_id == user_id,
        )
        .first()
    )

    if participant is None:
        raise HTTPException(
            status_code=404,
            detail="Participant not found",
        )

    chat_service.remove_participant(
        db=db,
        room_id=room_id,
        user_id=user_id,
    )

    return {
        "success": True,
        "message": "Participant removed",
    }

# ==========================================================
# User Presence
# ==========================================================

@router.get(
    "/presence/{user_id}",
)
def get_presence(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
):
    return {
        "user_id": user_id,
        "online": redis_service.is_online(user_id),
        "last_seen": redis_service.get_last_seen(user_id),
    }
