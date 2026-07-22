"""
app/services/redis_service.py

Production Redis Service

Responsibilities:
- Manage Redis connection
- Publish messages
- Subscribe to channels
- Store online users
- Store last seen timestamps
- Remove offline users
- Health check

No business logic should be placed here.
"""

import logging
import os
from datetime import datetime, timezone

import redis
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class RedisService:
    """Singleton Redis connection manager."""

    def __init__(self) -> None:
        self.host = os.getenv("REDIS_HOST", "redis")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.db = int(os.getenv("REDIS_DB", "0"))
        self.password = os.getenv("REDIS_PASSWORD", None)

        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30,
        )

    def ping(self) -> bool:
        """Check Redis availability."""
        try:
            return self.client.ping()
        except redis.RedisError as exc:
            logger.error("Redis ping failed: %s", exc)
            return False

    def publish(self, channel: str, message: str) -> bool:
        """Publish a message to a Redis channel."""
        try:
            self.client.publish(channel, message)
            return True
        except redis.RedisError as exc:
            logger.error("Redis publish failed: %s", exc)
            return False

    def subscribe(self, channel: str):
        """Subscribe to a Redis channel."""
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    def set_online(self, user_id: int) -> bool:
        """Mark a user as online."""
        try:
            self.client.sadd("online_users", user_id)
            return True
        except redis.RedisError as exc:
            logger.error("Failed to set user online: %s", exc)
            return False

    def set_offline(self, user_id: int) -> bool:
        """Remove a user from the online set."""
        try:
            self.client.srem("online_users", user_id)
            return True
        except redis.RedisError as exc:
            logger.error("Failed to remove user: %s", exc)
            return False

    def is_online(self, user_id: int) -> bool:
        """Check if a user is online."""
        try:
            return self.client.sismember("online_users", user_id)
        except redis.RedisError:
            return False

    def get_online_users(self) -> list[str]:
        """Return all currently online users."""
        try:
            return list(self.client.smembers("online_users"))
        except redis.RedisError:
            return []

    def set_last_seen(self, user_id: int) -> bool:
        """Store the user's last seen timestamp."""
        try:
            self.client.hset(
                "last_seen",
                str(user_id),
                datetime.now(timezone.utc).isoformat(),
            )
            return True
        except redis.RedisError as exc:
            logger.error("Failed to set last seen: %s", exc)
            return False

    def get_last_seen(self, user_id: int) -> str | None:
        """Return the user's last seen timestamp."""
        try:
            return self.client.hget("last_seen", str(user_id))
        except redis.RedisError as exc:
            logger.error("Failed to get last seen: %s", exc)
            return None

    def delete_key(self, key: str) -> bool:
        """Delete a Redis key."""
        try:
            self.client.delete(key)
            return True
        except redis.RedisError:
            return False


redis_service = RedisService()