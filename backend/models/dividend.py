from sqlalchemy import Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Dividend(Base):
    __tablename__ = "dividend"
    __table_args__ = (
        UniqueConstraint("symbol", "ex_date", name="uq_dividend"),
        Index("ix_dividend_symbol", "symbol"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    ex_date: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD", server_default="USD")
    updated_ts: Mapped[int] = mapped_column(Integer, nullable=False)
