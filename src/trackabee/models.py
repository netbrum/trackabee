from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Tracker(Base):
    __tablename__ = "tracker"
    __table_args__ = (Index("tracker_discord_user_id_IDX", "discord_user_id"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    discord_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    trend: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    goal: Mapped[int | None] = mapped_column(Integer)
    ends_at: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    points: Mapped[list[TrackerPoint]] = relationship(
        back_populates="tracker",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TrackerPoint(Base):
    __tablename__ = "tracker_point"
    __table_args__ = (Index("tracker_point_tracker_id_IDX", "tracker_id"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    tracker_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey(
            "tracker.id",
            name="tracker_point_tracker_FK",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        "timestamp",
        DateTime,
        nullable=False,
    )

    tracker: Mapped[Tracker] = relationship(back_populates="points")
