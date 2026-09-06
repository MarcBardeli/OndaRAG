import sqlite3
from datetime import datetime


DB_PATH = "chat.db"


def init_db():

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            conversation_id TEXT NOT NULL,

            role TEXT NOT NULL,

            content TEXT NOT NULL,

            created_at TEXT NOT NULL

        )
    """)

    conn.commit()
    conn.close()


def save_message(
    conversation_id,
    role,
    content
):

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO messages
        (
            conversation_id,
            role,
            content,
            created_at
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            conversation_id,
            role,
            content,
            datetime.now().isoformat()
        )
    )

    conn.commit()
    conn.close()


def get_messages(
    conversation_id
):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        """
        SELECT
            role,
            content

        FROM messages

        WHERE conversation_id = ?

        ORDER BY id ASC
        """,
        (conversation_id,)
    )


    messages = [

        {
            "role": role,
            "content": content
        }

        for role, content in cursor.fetchall()

    ]


    conn.close()

    return messages