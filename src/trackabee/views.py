import discord
from sqlalchemy import delete, update

from trackabee.db import Session, get_tracker
from trackabee.models import Tracker, TrackerPoint
from trackabee.responses import followup_chart, not_found


class OverwriteView(discord.ui.View):
    def __init__(self, user_id: int, tracker_id: str, point_id: str, value: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.tracker_id = tracker_id
        self.point_id = point_id
        self.value = value

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This prompt isn't for you", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Overwrite", style=discord.ButtonStyle.danger)
    async def overwrite(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        async with Session() as db:
            await db.execute(
                update(TrackerPoint)
                .values({"value": self.value})
                .where(TrackerPoint.id == self.point_id)
            )
            await db.commit()

            tracker = await get_tracker(db, self.tracker_id, self.user_id)

            if not tracker:
                return await not_found(interaction)

        await interaction.response.edit_message(content="Success", view=None)
        await followup_chart(interaction, tracker)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.edit_message(content="No changes made", view=None)


class RemoveView(discord.ui.View):
    def __init__(self, user_id: int, tracker_id: str):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.tracker_id = tracker_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This prompt isn't for you", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.danger)
    async def overwrite(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        async with Session() as db:
            await db.execute(
                delete(Tracker).where(
                    Tracker.id == self.tracker_id,
                    Tracker.discord_user_id == self.user_id,
                )
            )
            await db.commit()

        await interaction.response.edit_message(content="Removed tracker", view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.edit_message(content="No changes made", view=None)
