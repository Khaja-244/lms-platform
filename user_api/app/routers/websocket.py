"""
app/routers/websocket.py

Production WebSocket Routes
"""

import logging

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from app.auth import get_user_from_token
from app.database import SessionLocal
from app.services.chat_service import chat_service
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["WebSocket"],
)


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    db = SessionLocal()
    user = None
    try:
        user = get_user_from_token(token=token, db=db)
        await websocket_manager.connect(
            websocket=websocket,
            room_id=0,
            user_id=user.id,
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if user is not None:
            await websocket_manager.disconnect(websocket, 0, user.id)
    except Exception as exc:
        logger.exception("Notification WebSocket error: %s", exc)
        if user is not None:
            await websocket_manager.disconnect(websocket, 0, user.id)
        try:
            await websocket.close(code=1008)
        except Exception:
            pass
    finally:
        db.close()


@router.websocket("/ws/chat/{room_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id: int,
):
    """
    Chat WebSocket.

    Handles:
    - JWT authentication
    - Room authorization
    - Room connection
    - Message receive loop
    - Typing indicators
    - Online/offline tracking
    """

    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    db = SessionLocal()

    try:

        user = get_user_from_token(
            token=token,
            db=db,
        )

        if not chat_service.is_room_participant(
            db=db,
            room_id=room_id,
            user_id=user.id,
        ):
            logger.warning(
                "Unauthorized room access: user=%s room=%s",
                user.id,
                room_id,
            )

            await websocket.close(code=1008)
            return

        await websocket_manager.connect(
            websocket=websocket,
            room_id=room_id,
            user_id=user.id,
        )

        await websocket_manager.receive_loop(
            websocket=websocket,
            room_id=room_id,
            user_id=user.id,
        )

    except Exception as exc:

        logger.exception(
            "WebSocket authentication error: %s",
            exc,
        )

        await websocket.close(code=1008)

    finally:

        db.close()
