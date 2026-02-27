from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Watchlist(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market: Mapped[str] = mapped_column(String(10), nullable=False)  # A | US | HK | ETF
    added_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
