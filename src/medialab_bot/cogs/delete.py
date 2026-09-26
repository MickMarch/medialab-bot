import discord
from discord import app_commands
from discord.ext import commands

from medialab_bot.client import OrchestratorClient
from medialab_bot.constants import DISCORD_SELECT_MAX_OPTIONS
from medialab_bot.views.delete import DeleteSelectView

_DELETED_STATUS = "DELETED"


class DeleteCog(commands.Cog):
    def __init__(self, client: OrchestratorClient) -> None:
        self._client = client

    @app_commands.command(
        name="delete",
        description="Undo a download: remove it from qBittorrent, disk and Jellyfin",
    )
    async def delete(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        response = await self._client.list_jobs()

        if response is None:
            await interaction.followup.send("Failed to fetch jobs.", ephemeral=True)
            return

        candidates = [j for j in response.jobs if j.status != _DELETED_STATUS][
            :DISCORD_SELECT_MAX_OPTIONS
        ]
        if not candidates:
            await interaction.followup.send("Nothing to delete.", ephemeral=True)
            return

        await interaction.followup.send(
            "Pick the download to delete. You will see exactly what goes before confirming.",
            view=DeleteSelectView(self._client, candidates),
            ephemeral=True,
        )
