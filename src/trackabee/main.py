import uuid
from datetime import UTC, datetime
from typing import Literal

import discord
from dateutil.parser import parse
from discord import app_commands
from sqlalchemy import or_, select

from trackabee.db import Session, get_tracker
from trackabee.models import Tracker, TrackerPoint
from trackabee.responses import not_found, send_chart
from trackabee.settings import Settings
from trackabee.views import OverwriteView, RemoveView

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


@tree.command(name="add", description="Add tracker")
@app_commands.describe(
    name="Name",
    unit="Unit (words, steps, etc.)",
    trend="Up/Down",
    end="End (date)",
    goal="Goal (number)",
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

    await interaction.response.send_message("Success", ephemeral=True)


@tree.command(name="edit", description="Edit tracker")
@app_commands.describe(
    name="Name",
    unit="Unit (words, steps, etc.)",
    trend="Up/Down",
    end="End (date)",
    goal="Goal (number)",
)
async def edit(
    interaction: discord.Interaction,
    tracker: str,
    name: str,
    unit: str,
    trend: Literal["Up", "Down"] | None,
    end: str | None,
    goal: int | None,
) -> None:
    async with Session() as db:
        t = await get_tracker(db, tracker, interaction.user.id)

        if not t:
            return await not_found(interaction)

        t.name = name
        t.unit = unit
        t.trend = trend.lower() if trend else "up"
        t.ends_at = parse(end).date() if end else None
        t.goal = goal

        await db.commit()

    await interaction.response.send_message("Success", ephemeral=True)


@tree.command(name="remove", description="Remove tracker")
async def remove(interaction: discord.Interaction, tracker: str) -> None:
    await interaction.response.send_message(
        "Are you sure?", ephemeral=True, view=RemoveView(interaction.user.id, tracker)
    )


@tree.command(name="show", description="Show tracker chart")
async def show(interaction: discord.Interaction, tracker: str) -> None:
    async with Session() as db:
        t = await get_tracker(db, tracker, interaction.user.id)

    if not t:
        return await not_found(interaction)

    await send_chart(interaction, t)


@tree.command(name="log", description="Log progress")
@app_commands.describe(value="Value")
async def log(interaction: discord.Interaction, tracker: str, value: int) -> None:
    async with Session() as db:
        t = await get_tracker(db, tracker, interaction.user.id)

        if not t:
            return await not_found(interaction)

        timestamp = interaction.created_at.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        existing = await db.scalar(
            select(TrackerPoint).where(
                TrackerPoint.tracker_id == t.id, TrackerPoint.timestamp == timestamp
            )
        )

        if existing:
            await interaction.response.send_message(
                "You've already logged todays progress, do you want to overwrite?",
                ephemeral=True,
                view=OverwriteView(interaction.user.id, tracker, existing.id, value),
            )
            return

        point = TrackerPoint(
            id=str(uuid.uuid4()),
            tracker_id=t.id,
            value=value,
            timestamp=timestamp,
        )

        db.add(point)
        await db.commit()

    t.points.append(point)

    if len(t.points) == 1:
        await interaction.response.send_message(
            "First point in this tracker, Trackabee wishes you good luck on your journey!"
        )
    else:
        await send_chart(interaction, t)


@tree.command(name="pop", description="Remove last point")
async def pop(interaction: discord.Interaction, tracker: str) -> None:
    async with Session() as db:
        t = await get_tracker(db, tracker, interaction.user.id)

        if not t:
            return await not_found(interaction)

        point = await db.scalar(
            select(TrackerPoint).order_by(TrackerPoint.timestamp.desc()).limit(1)
        )
        await db.delete(point)
        await db.commit()

    if t.points:
        t.points.pop()

    if t.points:
        await send_chart(interaction, t)
    else:
        await interaction.response.send_message(
            "Popped last point in tracker", ephemeral=True
        )


@show.autocomplete("tracker")
@edit.autocomplete("tracker")
@remove.autocomplete("tracker")
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
    timestamp = interaction.created_at.replace(
        hour=0, minute=0, second=0, microsecond=0
    ).astimezone(UTC)

    async with Session() as db:
        trackers = await db.scalars(
            select(Tracker).where(
                Tracker.discord_user_id == interaction.user.id,
                or_(Tracker.ends_at > timestamp, Tracker.ends_at.is_(None)),
            )
        )

    return [
        app_commands.Choice(name=tracker.name, value=tracker.id)
        for tracker in trackers
        if current.lower() in tracker.name.lower()
    ]


if __name__ == "__main__":
    client.run(Settings().TOKEN)
