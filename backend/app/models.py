from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
from typing import Optional

class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    dataset_size_mb: Mapped[int] = mapped_column(Integer)
    scenario: Mapped[str] = mapped_column(String(40), default="NORMAL")
    target_rto_seconds: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="CREATED")
    backup_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    restore_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    integrity_status: Mapped[str] = mapped_column(String(30), default="NOT_TESTED")
    rto_status: Mapped[str] = mapped_column(String(30), default="NOT_EVALUATED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
