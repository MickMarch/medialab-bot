import discord

from medialab_bot.client import OrchestratorClient
from medialab_bot.constants import DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH
from medialab_bot.schemas.jobs import JobView


class JobRetryView(discord.ui.View):
    """A select menu to retry a failed pipeline job from its last good state."""

    def __init__(self, client: OrchestratorClient, failed_jobs: list[JobView]) -> None:
        super().__init__()
        self._client = client
        self._jobs = {j.torrent_hash: j for j in failed_jobs}

        options = [
            discord.SelectOption(
                label=(j.resolved_title or j.release_name or j.torrent_hash)[
                    :DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH
                ],
                value=j.torrent_hash,
                description=(j.last_error or "")[:DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH],
            )
            for j in failed_jobs
        ]
        self.select = discord.ui.Select(placeholder="Retry a failed job...", options=options)
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        try:
            torrent_hash = interaction.data["values"][0]
        except (KeyError, IndexError):
            await interaction.response.send_message(
                "Something went wrong with your selection. Please try again.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        job = await self._client.retry_job(torrent_hash)
        if job is None:
            await interaction.followup.send("Retry request failed.", ephemeral=True)
            return

        await interaction.followup.send(
            f"Retried job `{torrent_hash}` - now **{job.status}**.",
            ephemeral=True,
        )
