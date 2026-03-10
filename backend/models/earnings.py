from sqlalchemy import Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Earnings(Base):
    __tablename__ = "earnings"
    __table_args__ = (
        UniqueConstraint("symbol", "period_end", "period_type", name="uq_earnings"),
        Index("ix_earnings_symbol", "symbol"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    period_end: Mapped[str] = mapped_column(String(10), nullable=False)
    period_type: Mapped[str] = mapped_column(String(10), nullable=False)
    revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    eps: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    operating_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_ts: Mapped[int] = mapped_column(Integer, nullable=False)
