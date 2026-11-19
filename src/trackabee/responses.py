import discord

from trackabee.chart import ChartNoPointsError, generate_chart
from trackabee.models import Tracker


async def not_found(interaction: discord.Interaction, ephemeral=True) -> None:
    await interaction.response.send_message(
        "Couldn't find tracker", ephemeral=ephemeral
    )


async def send_chart(interaction: discord.Interaction, tracker: Tracker):
    try:
        image = generate_chart(tracker)

        await interaction.response.send_message(
            file=discord.File(image, filename="chart.png")
        )
    except ChartNoPointsError:
        await interaction.response.send_message("No data in tracker", ephemeral=True)
