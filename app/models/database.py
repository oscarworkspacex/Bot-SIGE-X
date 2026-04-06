from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Classification(Base):
    __tablename__ = "classifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_chat_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    telegram_message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    capa1_positivo: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    capa1_equipo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    capa1_tabla: Mapped[str | None] = mapped_column(String(200), nullable=True)
    capa1_confianza: Mapped[float | None] = mapped_column(Float, nullable=True)
    capa1_motivo: Mapped[str | None] = mapped_column(String(300), nullable=True)

    capa2_equipo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    capa2_tabla: Mapped[str | None] = mapped_column(String(200), nullable=True)
    capa2_tarea: Mapped[str | None] = mapped_column(Text, nullable=True)

    decision_final: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Classification id={self.id} chat={self.telegram_chat_id} "
            f"c1={self.capa1_positivo} c2_eq={self.capa2_equipo}>"
        )
