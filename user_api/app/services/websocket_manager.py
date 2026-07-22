"""
app/services/websocket_manager.py

Production WebSocket Manager

Responsibilities
----------------
- Manage active WebSocket connections
- Join/Leave chat rooms
- Broadcast messages
- Redis Pub/Sub integration
- Online user tracking
"""

import asyncio
import json
import logging
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect
from app.database import SessionLocal
from app.services.chat_service import chat_service
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Singleton WebSocket manager.

    Stores:

    room_connections
        room_id -> list[WebSocket]

    user_connections
        user_id -> WebSocket
    """

    def __init__(self):

        self.room_connections: dict[int, list[WebSocket]] = defaultdict(list)

        self.user_connections: dict[int, set[WebSocket]] = defaultdict(set)

        self.redis_channel = "lms_chat"

        self.redis_listener_started = False

    async def connect(
        self,
        websocket: WebSocket,
        room_id: int,
        user_id: int,
    ):

        await websocket.accept()

        if websocket not in self.room_connections[room_id]:
            self.room_connections[room_id].append(websocket)

        self.user_connections[user_id].add(websocket)

        redis_service.set_online(user_id)
        redis_service.publish(
            self.redis_channel,
            json.dumps({
                "event": "presence",
                "room_id": room_id,
                "user_id": user_id,
                "online": True,
                "last_seen": None,
                "broadcast": True,
            }),
        )

        logger.info(
            "User %s joined room %s",
            user_id,
            room_id,
        )

        if not self.redis_listener_started:
            self.redis_listener_started = True
            asyncio.create_task(self.redis_listener())

    async def disconnect(
        self,
        websocket: WebSocket,
        room_id: int,
        user_id: int,
    ):

        if room_id in self.room_connections:

            if websocket in self.room_connections[room_id]:
                self.room_connections[room_id].remove(websocket)

            if not self.room_connections[room_id]:
                del self.room_connections[room_id]

        connections = self.user_connections.get(user_id, set())
        connections.discard(websocket)
        if not connections:
            self.user_connections.pop(user_id, None)
            redis_service.set_offline(user_id)
            redis_service.set_last_seen(user_id)
            redis_service.publish(
                self.redis_channel,
                json.dumps({
                    "event": "presence",
                    "room_id": room_id,
                    "user_id": user_id,
                    "online": False,
                    "last_seen": redis_service.get_last_seen(user_id),
                    "broadcast": True,
                }),
            )

        logger.info(
            "User %s left room %s",
            user_id,
            room_id,
        )

    async def send_to_room(
        self,
        room_id: int,
        payload: dict,
    ):

        dead_connections = []

        for websocket in self.room_connections.get(room_id, []):

            try:

                await websocket.send_json(payload)

            except WebSocketDisconnect:

                dead_connections.append(websocket)

            except Exception:

                dead_connections.append(websocket)

        for websocket in dead_connections:

            if websocket in self.room_connections.get(room_id, []):

                self.room_connections[room_id].remove(websocket)

        if room_id in self.room_connections and not self.room_connections[room_id]:
            del self.room_connections[room_id]

    async def send_to_user(
        self,
        user_id: int,
        payload: dict,
    ):

        sockets = self.user_connections.get(user_id, set())
        if not sockets:
            return
        for socket in list(sockets):
            try:
                await socket.send_json(payload)
            except Exception:
                sockets.discard(socket)

    async def broadcast(
        self,
        payload: dict,
    ):

        for sockets in list(self.user_connections.values()):
            for websocket in list(sockets):
                try:
                    await websocket.send_json(payload)
                except Exception:
                    pass
             
    async def redis_listener(self):
        """
        Listen for Redis Pub/Sub messages and broadcast them
        to all connected WebSocket clients in the target room.
        """

        pubsub = redis_service.subscribe(self.redis_channel)

        while True:

            try:

                message = pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1,
                )

                if message is None:
                    await asyncio.sleep(0.05)
                    continue

                data = json.loads(message["data"])

                user_ids = data.pop("user_ids", None)
                if user_ids:
                    for target_user_id in user_ids:
                        await self.send_to_user(int(target_user_id), data)
                    continue

                if data.pop("broadcast", False):
                    await self.broadcast(data)
                    continue

                room_id = data.get("room_id")

                if room_id is None:
                    continue

                await self.send_to_room(
                    room_id=int(room_id),
                    payload=data,
                )

            except Exception as exc:

                logger.exception(
                    "Redis listener error: %s",
                    exc,
                )

                await asyncio.sleep(1)

    async def receive_loop(
        self,
        websocket: WebSocket,
        room_id: int,
        user_id: int,
    ):
        """
        Keep the websocket alive by continuously
        receiving client messages.

        Supports:
        - typing_start
        - typing_stop
        - text/file messages
        """

        try:

            while True:

                payload = await websocket.receive_json()

                event = payload.get("event")

                if event in ("delivered", "read"):
                    message_id = int(payload.get("message_id", 0))
                    if message_id:
                        db = SessionLocal()
                        try:
                            if event == "delivered":
                                changed = chat_service.mark_delivered(db, message_id, user_id)
                                message_ids = [message_id] if changed else []
                            else:
                                message = chat_service.get_message(db, message_id)
                                message_ids = (
                                    chat_service.mark_room_read(db, room_id, user_id)
                                    if message and message.room_id == room_id else []
                                )
                            if message_ids:
                                redis_service.publish(
                                    self.redis_channel,
                                    json.dumps({
                                        "event": event,
                                        "room_id": room_id,
                                        "user_id": user_id,
                                        "message_ids": message_ids,
                                    }),
                                )
                        finally:
                            db.close()
                    continue

                # ------------------------------------
                # Typing Indicator
                # ------------------------------------
                if event in ("typing_start", "typing_stop"):

                    typing_payload = {
                        "event": event,
                        "room_id": room_id,
                        "user_id": user_id,
                        "user_name": payload.get("user_name", "Someone"),
                    }

                    redis_service.publish(
                        self.redis_channel,
                        json.dumps(typing_payload),
                    )

                    continue

                # ------------------------------------
                # Normal Chat Message
                # ------------------------------------

                message = payload.get("message", "").strip()

                if not message:
                    continue

                db = SessionLocal()

                try:

                    saved = chat_service.send_message(
                        db=db,
                        room_id=room_id,
                        sender_id=user_id,
                        message=message,
                        message_type=payload.get(
                            "message_type",
                            "text",
                        ),
                    )

                    db.commit()

                    db.refresh(saved)

                    out = chat_service.message_payload(db, saved, user_id)
                    out["event"] = "message"
                    for field in ("created_at", "delivered_at", "read_at"):
                        value = out.get(field)
                        if value is not None:
                            out[field] = value.isoformat()

                except Exception as exc:

                    db.rollback()

                    logger.exception(
                        "Failed to save websocket message: %s",
                        exc,
                    )

                    raise

                finally:

                    db.close()

                redis_service.publish(
                    self.redis_channel,
                    json.dumps(out),
                )

        except WebSocketDisconnect:

            await self.disconnect(
                websocket,
                room_id,
                user_id,
            )

        except Exception as exc:

            logger.exception(
                "WebSocket receive error: %s",
                exc,
            )

            await self.disconnect(
                websocket,
                room_id,
                user_id,
            )

    async def close_room(
        self,
        room_id: int,
    ):
        """
        Close every websocket connected
        to a room.
        """

        for websocket in list(
            self.room_connections.get(room_id, [])
        ):

            try:
                await websocket.close()
            except Exception:
                pass

        self.room_connections.pop(room_id, None)

    def online_users(self) -> list[str]:
        """
        Return all currently online users.
        """

        return redis_service.get_online_users()

    def is_online(
        self,
        user_id: int,
    ) -> bool:

        return redis_service.is_online(user_id)


websocket_manager = WebSocketManager()         
