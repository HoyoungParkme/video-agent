"""대화 턴 테이블(VA-DOM-003 chat_turns)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Identity, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ChatTurnRow(Base):
    """질문 하나와 답(DOM-002 2.4 ChatTurn). 답을 받은 뒤 한 번 저장한다."""

    __tablename__ = "chat_turns"
    __table_args__ = (Index("ix_chat_turns_video_id_asked_at", "video_id", "asked_at"),)

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    cited_secs: Mapped[list[float]] = mapped_column(JSONB)
    model: Mapped[str] = mapped_column(String(50))
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
