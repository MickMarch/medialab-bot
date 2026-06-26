import discord
from discord import app_commands
from discord.ext import commands

from medialab_bot.client import OrchestratorClient
from medialab_bot.embeds import jobs_embed
from medialab_bot.views.jobs import JobRetryView

_FAILED_STATUS = "FAILED"


class JobsCog(commands.Cog):
    def __init__(self, client: OrchestratorClient) -> None:
        self._client = client

    @app_commands.command(name="jobs", description="List media pipeline jobs")
    @app_commands.describe(status="Filter by status (e.g. DOWNLOADING, FAILED, DONE)")
    async def jobs(self, interaction: discord.Interaction, status: str | None = None) -> None:
        await interaction.response.defer(ephemeral=True)
        response = await self._client.list_jobs(status=status)

        if response is None:
            await interaction.followup.send("Failed to fetch jobs.", ephemeral=True)
            return

        if not response.jobs:
            await interaction.followup.send("No jobs found.", ephemeral=True)
            return

        # Offer a retry control for any failed job in the result set. discord.py
        # rejects view=None (it expects a View or the param omitted entirely), so
        # only pass view when there is one.
        failed = [j for j in response.jobs if j.status == _FAILED_STATUS]
        kwargs: dict = {"embed": jobs_embed(response), "ephemeral": True}
        if failed:
            kwargs["view"] = JobRetryView(self._client, failed)
        await interaction.followup.send(**kwargs)
