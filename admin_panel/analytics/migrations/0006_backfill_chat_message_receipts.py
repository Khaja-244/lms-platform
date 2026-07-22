from django.db import migrations


BACKFILL_RECEIPTS = """
INSERT INTO chat_message_receipts (message_id, user_id, delivered_at, read_at)
SELECT message.id, participant.user_id, message.created_at, message.created_at
FROM chat_messages AS message
INNER JOIN chat_participants AS participant ON participant.room_id = message.room_id
WHERE participant.user_id <> message.sender_id
ON CONFLICT (message_id, user_id) DO NOTHING;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0005_chatmessagereceipt"),
    ]

    operations = [
        migrations.RunSQL(BACKFILL_RECEIPTS, migrations.RunSQL.noop),
    ]
