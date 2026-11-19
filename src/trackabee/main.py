import uuid
from datetime import UTC, datetime
from typing import Literal

import discord
from dateutil.parser import parse
from discord import app_commands
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from trackabee.db import Session
from trackabee.models import Tracker, TrackerPoint
from trackabee.responses import not_found, send_chart
from trackabee.settings import Settings

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


async def get_tracker(tracker_id: str, discord_user_id: int) -> Tracker | None:
    async with Session() as db:
        tracker = await db.scalar(
            select(Tracker)
            .options(selectinload(Tracker.points))
            .where(Tracker.id == tracker_id, Tracker.discord_user_id == discord_user_id)
        )
        return tracker


@tree.command(name="add", description="Add tracker")
@app_commands.describe(
    name="Name",
    end="End (date)",
    goal="Goal (number)",
    trend="Up/Down",
    unit="Unit (words, steps, etc.)",
)
async def add(
    interaction: discord.Interaction,
    name: str,
    unit: str,
    trend: Literal["Up", "Down"] | None,
    end: str | None,
    goal: int | None,
) -> None:
    async with Session() as db:
        db.add(
            Tracker(
                id=str(uuid.uuid4()),
                discord_user_id=interaction.user.id,
                name=name,
                trend=trend.lower() if trend else "up",
                unit=unit,
                goal=goal,
                ends_at=parse(end).date() if end else None,
                created_at=datetime.now(UTC),
            )
        )

        await db.commit()

    await interaction.response.send_message("✅ Success", ephemeral=True)


@tree.command(name="show", description="Show tracker chart")
async def show(interaction: discord.Interaction, tracker: str) -> None:
    t = await get_tracker(tracker, interaction.user.id)

    if not t:
        return await not_found(interaction)

    await send_chart(interaction, t)


@tree.command(name="log", description="Log progress")
@app_commands.describe(value="Value")
async def log(interaction: discord.Interaction, tracker: str, value: int) -> None:
    t = await get_tracker(tracker, interaction.user.id)

    if not t:
        return await not_found(interaction)

    async with Session() as db:
        point = TrackerPoint(
            id=str(uuid.uuid4()),
            tracker_id=t.id,
            value=value,
            timestamp=interaction.created_at.replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
        )
        db.add(point)
        await db.commit()

    t.points.append(point)

    await send_chart(interaction, t)


@tree.command(name="pop", description="Remove last point")
async def pop(interaction: discord.Interaction, tracker: str) -> None:
    t = await get_tracker(tracker, interaction.user.id)

    if not t:
        return await not_found(interaction)

    async with Session() as db:
        point = await db.scalar(
            select(TrackerPoint).order_by(TrackerPoint.timestamp.desc()).limit(1)
        )
        await db.delete(point)
        await db.commit()

    if t.points:
        t.points.pop()

    await send_chart(interaction, t)


@show.autocomplete("tracker")
async def all_trackers_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    async with Session() as db:
        trackers = await db.scalars(
            select(Tracker).where(Tracker.discord_user_id == interaction.user.id)
        )

    return [
        app_commands.Choice(name=tracker.name, value=tracker.id)
        for tracker in trackers
        if current.lower() in tracker.name.lower()
    ]


@log.autocomplete("tracker")
@pop.autocomplete("tracker")
async def active_trackers_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    async with Session() as db:
        trackers = await db.scalars(
            select(Tracker).where(
                Tracker.discord_user_id == interaction.user.id,
                or_(Tracker.ends_at > datetime.now(UTC), Tracker.ends_at.is_(None)),
            )
        )

    return [
        app_commands.Choice(name=tracker.name, value=tracker.id)
        for tracker in trackers
        if current.lower() in tracker.name.lower()
    ]


if __name__ == "__main__":
    client.run(Settings().TOKEN)
