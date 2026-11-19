from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from trackabee.models import Tracker

engine = create_async_engine("sqlite+aiosqlite:///trackabee.db")

Session = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


async def get_tracker(
    db: AsyncSession, tracker_id: str, discord_user_id: int
) -> Tracker | None:
    tracker = await db.scalar(
        select(Tracker)
        .options(selectinload(Tracker.points))
        .where(Tracker.id == tracker_id, Tracker.discord_user_id == discord_user_id)
    )
    return tracker
