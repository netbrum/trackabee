import logging

import discord

from trackabee.chart import ChartNoPointsError, generate_chart
from trackabee.models import Tracker


async def not_found(
    interaction: discord.Interaction, tracker_id: str, ephemeral=True
) -> None:
    logging.info(f"{interaction.user.name}::{tracker_id}::not_found")
    await interaction.response.send_message(
        "Couldn't find tracker", ephemeral=ephemeral
    )


async def send_chart(interaction: discord.Interaction, tracker: Tracker):
    try:
        image = generate_chart(tracker)

        logging.info(f"{interaction.user.name}::{tracker.id}::chart")

        await interaction.response.send_message(
            file=discord.File(image, filename="chart.png")
        )
    except ChartNoPointsError:
        await interaction.response.send_message("No data in tracker", ephemeral=True)


async def followup_chart(interaction: discord.Interaction, tracker: Tracker):
    try:
        image = generate_chart(tracker)

        logging.info(f"{interaction.user.name}::{tracker.id}::chart")

        await interaction.followup.send(
            content=f"{interaction.user.mention} Log overwritten, here's the updated chart",
            file=discord.File(image, filename="chart.png"),
        )
    except ChartNoPointsError:
        await interaction.followup.send("No data in tracker", ephemeral=True)
