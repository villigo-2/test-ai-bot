from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


_MAX_HISTORY: int = 10
_dialog_state: Dict[int, List[Dict[str, Any]]] = {}
_last_context: Dict[int, Dict[str, str]] = {}


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


def set_last_context(chat_id: int, query: str, geo_iso: str) -> None:
    _last_context[chat_id] = {"query": query, "geo_iso": geo_iso}


def get_last_context(chat_id: int) -> Optional[Tuple[str, str]]:
    ctx = _last_context.get(chat_id)
    if not ctx:
        return None
    return ctx.get("query", ""), ctx.get("geo_iso", "")


