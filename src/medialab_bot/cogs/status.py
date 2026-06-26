import discord
from discord import app_commands
from discord.ext import commands

from medialab_bot.client import OrchestratorClient
from medialab_bot.embeds import storage_embed, transfers_embed


class StatusCog(commands.Cog):
    def __init__(self, client: OrchestratorClient) -> None:
        self._client = client

    @app_commands.command(name="transfers", description="List active torrent transfers")
    async def transfers(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        response = await self._client.get_transfers()

        if response is None:
            await interaction.followup.send("Failed to fetch transfers.", ephemeral=True)
            return

        if not response.transfers.data:
            await interaction.followup.send("No active transfers.", ephemeral=True)
            return

        await interaction.followup.send(embed=transfers_embed(response), ephemeral=True)

    @app_commands.command(name="storage", description="Show disk usage")
    async def storage(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        response = await self._client.get_storage()

        if response is None:
            await interaction.followup.send("Failed to fetch storage info.", ephemeral=True)
            return

        await interaction.followup.send(embed=storage_embed(response), ephemeral=True)
