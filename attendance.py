import asyncio
from datetime import datetime
from typing import Dict, Optional, Set

class Session:
    def __init__(self, group_chat_id: int, message_id: int, lesson_title: str, admin_chat_id: int):
        self.group_chat_id = group_chat_id          # ID группы, где идёт опрос
        self.message_id = message_id                # ID сообщения с кнопкой
        self.lesson_title = lesson_title            # Название занятия
        self.admin_chat_id = admin_chat_id          # ID админа для отчёта
        self.active = True
        self.start_time = datetime.now()
        self.marked_users: Set[str] = set()         # username отметившихся
        self.students_set: Optional[Set[str]] = None # все допустимые username из таблицы
        self.lock = asyncio.Lock()

# Словарь сессий, ключ — group_chat_id (так как в группе может быть только одна активная сессия)
_sessions: Dict[int, Session] = {}

def get_session(group_chat_id: int) -> Optional[Session]:
    return _sessions.get(group_chat_id)

def set_session(group_chat_id: int, session: Session):
    _sessions[group_chat_id] = session

def delete_session(group_chat_id: int):
    _sessions.pop(group_chat_id, None)