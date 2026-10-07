from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DatasetImport(Base):
    __tablename__ = "dataset_imports"
    __table_args__ = {"schema": "research"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    issue_count: Mapped[int | None] = mapped_column(BigInteger)
    project_count: Mapped[int | None] = mapped_column(Integer)
    sprint_count: Mapped[int | None] = mapped_column(Integer)

