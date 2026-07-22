from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


CHAT_SQL = """
CREATE TABLE IF NOT EXISTS chat_rooms (
  id BIGSERIAL PRIMARY KEY, name VARCHAR(150), room_type VARCHAR(20) NOT NULL DEFAULT 'private',
  created_by BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS chat_participants (
  id BIGSERIAL PRIMARY KEY, room_id BIGINT NOT NULL REFERENCES chat_rooms(id) ON DELETE CASCADE,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE, joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_room_user UNIQUE(room_id, user_id)
);
CREATE TABLE IF NOT EXISTS chat_messages (
  id BIGSERIAL PRIMARY KEY, room_id BIGINT NOT NULL REFERENCES chat_rooms(id) ON DELETE CASCADE,
  sender_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE, message TEXT, message_type VARCHAR(20) NOT NULL DEFAULT 'text',
  file_name VARCHAR(255), file_url TEXT, is_deleted BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_room_created ON chat_messages(room_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_sender ON chat_messages(sender_id);
"""


class Migration(migrations.Migration):
    dependencies = [("analytics", "0002_notification_details_activity_ip"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.RunSQL(CHAT_SQL, reverse_sql=migrations.RunSQL.noop),
        migrations.SeparateDatabaseAndState(state_operations=[migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("room_id", models.BigIntegerField()), ("message", models.TextField(blank=True, null=True)),
                ("message_type", models.CharField(default="text", max_length=20)), ("file_name", models.CharField(blank=True, max_length=255, null=True)),
                ("file_url", models.TextField(blank=True, null=True)), ("is_deleted", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("sender", models.ForeignKey(db_column="sender_id", on_delete=django.db.models.deletion.DO_NOTHING, related_name="chat_messages", to=settings.AUTH_USER_MODEL)),
            ], options={"db_table": "chat_messages", "ordering": ["-created_at"], "managed": False},
        )]),
    ]
