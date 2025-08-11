from datetime import datetime
from typing import Any, Dict, List


_MAX_HISTORY: int = 10
_dialog_state: Dict[int, List[Dict[str, Any]]] = {}


def add_message(chat_id: int, role: str, content: str) -> None:
    messages = _dialog_state.setdefault(chat_id, [])
    messages.append({
        "role": role,
        "content": content,
        "ts": datetime.utcnow().isoformat(),
    })
    if len(messages) > _MAX_HISTORY:
        del messages[0 : len(messages) - _MAX_HISTORY]


def get_recent(chat_id: int, limit: int = 3) -> List[Dict[str, Any]]:
    return (_dialog_state.get(chat_id) or [])[-limit:]


