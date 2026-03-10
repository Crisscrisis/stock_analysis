from sqlalchemy import Boolean, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class IndexConstituent(Base):
    __tablename__ = "index_constituent"
    __table_args__ = (
        UniqueConstraint("index_name", "symbol", name="uq_index_constituent"),
        Index("ix_index_constituent_index_name", "index_name"),
        Index("ix_index_constituent_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    index_name: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    added_at: Mapped[float] = mapped_column(Float, nullable=False)
    removed_at: Mapped[float | None] = mapped_column(Float, nullable=True)
