"""
app/services/chat_service.py

Production Chat Service
"""

from datetime import datetime, timezone


from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    ChatMessage,
    ChatParticipant,
    ChatRoom,
    User,
    ChatMessageReceipt,
)
from app.services import notification_service
from app.services.redis_service import redis_service


class ChatService:

    @staticmethod
    def create_room(
        db: Session,
        creator_id: int,
        room_type: str,
        participant_ids: list[int],
        name: str | None = None,
    ) -> ChatRoom:

        if not participant_ids:
            raise ValueError(
                "At least one participant is required."
            )

        room = ChatRoom(
            name=name,
            room_type=room_type,
            created_by=creator_id,
        )

        db.add(room)
        db.flush()
        db.refresh(room)

        users = set(participant_ids)
        users.add(creator_id)

        for uid in users:
            db.add(
                ChatParticipant(
                    room_id=room.id,
                    user_id=uid,
                )
            )

        db.commit()
        db.refresh(room)

        return room

    @staticmethod
    def get_room(
        db: Session,
        room_id: int,
    ) -> ChatRoom | None:

        return (
            db.query(ChatRoom)
            .filter(ChatRoom.id == room_id)
            .first()
        )

    @staticmethod
    def get_user_rooms(
        db: Session,
        user_id: int,
    ) -> list[ChatRoom]:

        return (
            db.query(ChatRoom)
            .join(
                ChatParticipant,
                ChatParticipant.room_id == ChatRoom.id,
            )
            .filter(
                ChatParticipant.user_id == user_id,
            )
            .all()
        )
    
    @staticmethod
    def is_room_participant(
        db: Session,
        room_id: int,
        user_id: int,
    ) -> bool:
        """
        Check whether a user belongs to a chat room.
        """

        return (
            db.query(ChatParticipant)
            .filter(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user_id,
            )
            .first()
            is not None
        )

    @staticmethod
    def add_participant(
        db: Session,
        room_id: int,
        user_id: int,
    ) -> ChatParticipant:

        exists = (
            db.query(ChatParticipant)
            .filter(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user_id,
            )
            .first()
        )

        if exists:
            return exists

        participant = ChatParticipant(
            room_id=room_id,
            user_id=user_id,
        )

        db.add(participant)
        db.commit()
        db.refresh(participant)

        return participant

    @staticmethod
    def remove_participant(
        db: Session,
        room_id: int,
        user_id: int,
    ) -> None:

        participant = (
            db.query(ChatParticipant)
            .filter(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user_id,
            )
            .first()
        )

        if participant:
            db.delete(participant)
            db.commit()

    @staticmethod
    def send_message(
        db: Session,
        room_id: int,
        sender_id: int,
        message: str | None,
        message_type: str = "text",
        file_name: str | None = None,
        file_url: str | None = None,
    ) -> ChatMessage:

        room = (
            db.query(ChatRoom)
            .filter(ChatRoom.id == room_id)
            .first()
        )

        if room is None:
            raise ValueError("Chat room not found.")
        
        if not ChatService.is_room_participant(
            db=db,
            room_id=room_id,
            user_id=sender_id,
        ):
            raise PermissionError(
                "You are not a participant of this room."
            )

        chat = ChatMessage(
            room_id=room_id,
            sender_id=sender_id,
            message=message,
            message_type=message_type,
            file_name=file_name,
            file_url=file_url,
            created_at=datetime.now(timezone.utc),
        )

        db.add(chat)
        db.flush()
        sender = db.query(User).filter(
            User.id == sender_id
        ).first()
        recipient_ids = [
            row.user_id for row in db.query(ChatParticipant).filter(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id != sender_id,
            ).all()
        ]
        preview = (message or file_name or "New attachment").strip()[:120]
        recipients = db.query(User).filter(User.id.in_(recipient_ids)).all()
        now = datetime.now(timezone.utc)
        for recipient in recipients:
            db.add(ChatMessageReceipt(
                message_id=chat.id,
                user_id=recipient.id,
                delivered_at=now if redis_service.is_online(recipient.id) else None,
            ))
            notification_service.create_notification(
                db=db,
                user_id=recipient.id,
                title=f"New message from {sender.name if sender else 'a user'}",
                message=preview,
                notification_type="chat_message",
                link="/student/chat/" if recipient.role == "student" else "/instructor/dashboard/#notifications",
            )
        notification_service.NotificationService.notify_admins(
            db=db,
            title="Chat Activity",
            message=f"{sender.name if sender else 'A user'} sent a message in room #{room_id}.",
            notification_type="chat_message",
            link="/analytics/",
        )
        db.commit()
        db.refresh(chat)
        redis_service.publish(
            "lms_chat",
            __import__("json").dumps({
                "event": "notification",
                "user_ids": recipient_ids,
                "room_id": room_id,
                "title": f"New message from {sender.name if sender else 'a user'}",
                "message": preview,
                "sender_id": sender_id,
                "sender_name": sender.name if sender else "Unknown user",
            }),
        )
        return chat

    @staticmethod
    def get_message(db: Session, message_id: int) -> ChatMessage | None:
        return db.query(ChatMessage).filter(ChatMessage.id == message_id).first()

    @staticmethod
    def message_payload(
        db: Session,
        message: ChatMessage,
        viewer_id: int,
    ) -> dict:
        receipt = (
            db.query(ChatMessageReceipt)
            .filter(
                ChatMessageReceipt.message_id == message.id,
                ChatMessageReceipt.user_id != message.sender_id,
            )
            .order_by(ChatMessageReceipt.read_at.asc().nullsfirst())
            .first()
        )
        status = "sent"
        delivered_at = None
        read_at = None
        if receipt is not None:
            delivered_at = receipt.delivered_at
            read_at = receipt.read_at
            if receipt.read_at is not None:
                status = "read"
            elif receipt.delivered_at is not None:
                status = "delivered"
        return {
            "id": message.id,
            "room_id": message.room_id,
            "sender_id": message.sender_id,
            "sender_name": message.sender.name if message.sender else "Unknown user",
            "message": message.message,
            "message_type": message.message_type,
            "file_name": message.file_name,
            "file_url": message.file_url,
            "is_deleted": message.is_deleted,
            "created_at": message.created_at,
            "delivery_status": status if message.sender_id == viewer_id else "read",
            "delivered_at": delivered_at,
            "read_at": read_at,
        }

    @staticmethod
    def room_summary(db: Session, room: ChatRoom, viewer_id: int) -> dict:
        participant_rows = (
            db.query(ChatParticipant)
            .filter(ChatParticipant.room_id == room.id)
            .all()
        )
        participants = []
        other_names = []
        for row in participant_rows:
            user = row.user
            if user.id != viewer_id:
                other_names.append(user.name)
            participants.append({
                "id": user.id,
                "name": user.name,
                "role": user.role,
                "profile_picture": user.profile_picture or "",
                "online": redis_service.is_online(user.id),
                "last_seen": redis_service.get_last_seen(user.id),
            })
        last_message = (
            db.query(ChatMessage)
            .filter(ChatMessage.room_id == room.id, ChatMessage.is_deleted.is_(False))
            .order_by(ChatMessage.created_at.desc())
            .first()
        )
        unread_count = (
            db.query(ChatMessageReceipt)
            .join(ChatMessage, ChatMessage.id == ChatMessageReceipt.message_id)
            .filter(
                ChatMessage.room_id == room.id,
                ChatMessageReceipt.user_id == viewer_id,
                ChatMessageReceipt.read_at.is_(None),
            )
            .count()
        )
        display_name = room.name if room.room_type == "group" and room.name else ", ".join(other_names)
        return {
            "id": room.id,
            "name": room.name,
            "display_name": display_name or "Conversation",
            "room_type": room.room_type,
            "created_by": room.created_by,
            "created_at": room.created_at,
            "participants": participants,
            "unread_count": unread_count,
            "last_message": (
                (last_message.message or last_message.file_name or "Attachment")[:120]
                if last_message else ""
            ),
            "last_message_at": last_message.created_at if last_message else None,
        }

    @staticmethod
    def mark_delivered(db: Session, message_id: int, user_id: int) -> bool:
        receipt = db.query(ChatMessageReceipt).filter(
            ChatMessageReceipt.message_id == message_id,
            ChatMessageReceipt.user_id == user_id,
        ).first()
        if receipt is None:
            return False
        if receipt.delivered_at is None:
            receipt.delivered_at = datetime.now(timezone.utc)
            db.commit()
        return True

    @staticmethod
    def mark_room_read(db: Session, room_id: int, user_id: int) -> list[int]:
        now = datetime.now(timezone.utc)
        receipts = (
            db.query(ChatMessageReceipt)
            .join(ChatMessage, ChatMessage.id == ChatMessageReceipt.message_id)
            .filter(
                ChatMessage.room_id == room_id,
                ChatMessageReceipt.user_id == user_id,
                ChatMessageReceipt.read_at.is_(None),
            )
            .all()
        )
        message_ids = []
        for receipt in receipts:
            receipt.delivered_at = receipt.delivered_at or now
            receipt.read_at = now
            message_ids.append(receipt.message_id)
        if receipts:
            db.commit()
        return message_ids

    @staticmethod
    def upload_file(
        db: Session,
        room_id: int,
        sender_id: int,
        file_name: str,
        file_url: str,
    ) -> ChatMessage:

        return ChatService.send_message(
            db=db,
            room_id=room_id,
            sender_id=sender_id,
            message=file_name,
            message_type="doc",
            file_name=file_name,
            file_url=file_url,
        )

    @staticmethod
    def get_messages(
        db: Session,
        room_id: int,
        user_id: int,
    ) -> list[ChatMessage]:

        if not ChatService.is_room_participant(
            db=db,
            room_id=room_id,
            user_id=user_id,
        ):
            raise PermissionError(
                "You are not a participant of this room."
            )

    
        return (
            db.query(ChatMessage)
            .filter(
                ChatMessage.room_id == room_id,
                ChatMessage.is_deleted.is_(False),
            )
            .order_by(ChatMessage.created_at.asc())
            .all()
        )


    @staticmethod
    def get_messages_paginated(
        db: Session,
        room_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ChatMessage], int]:

        if not ChatService.is_room_participant(
            db=db,
            room_id=room_id,
            user_id=user_id,
        ):
            raise PermissionError(
                "You are not a participant of this room."
            )

        page = max(page, 1)
        page_size = max(1, min(page_size, 100))

        query = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.room_id == room_id,
                ChatMessage.is_deleted.is_(False),
            )
        )

        total = (
            db.query(func.count(ChatMessage.id))
            .filter(
                ChatMessage.room_id == room_id,
                ChatMessage.is_deleted.is_(False),
            )
            .scalar()
        )

        messages = (
            query.order_by(ChatMessage.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        messages.reverse()

        return messages, total


    @staticmethod
    def delete_message(
        db: Session,
        message_id: int,
        user_id: int,
    ) -> bool:

        message = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.id == message_id,
                ChatMessage.sender_id == user_id,
            )
            .first()
        )

        if message is None:
            return False

        message.is_deleted = True

        db.commit()

        return True

chat_service = ChatService()    
