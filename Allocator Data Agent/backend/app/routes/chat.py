"""Chat routes — thin HTTP layer, delegates to the chat service.

The chat service's ONLY tool is a read-only query against the local cache
(app/services/query_tool.py). Nothing on this path can reach the live
Allocator Admin API — that client lives solely in app/services/
allocator_admin_service.py, imported only by app/services/data_sync.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat as chat_service
from db.database import get_db

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def ask(
    body: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    answer = chat_service.answer_question(db, body.message)
    return ChatResponse(answer=answer)
