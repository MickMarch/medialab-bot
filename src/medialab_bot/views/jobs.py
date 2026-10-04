from collections.abc import Awaitable, Callable

import discord

from medialab_bot.client import OrchestratorClient
from medialab_bot.constants import DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH
from medialab_bot.schemas.jobs import JobView

_RETRY_PLACEHOLDER = "Retry a failed or flagged job..."
_DISMISS_PLACEHOLDER = "Dismiss a flagged job (files untouched)..."
_SELECTION_ERROR = "Something went wrong with your selection. Please try again."

JobAction = Callable[[str], Awaitable[JobView | None]]


class JobRetryView(discord.ui.View):
    """Two select menus over the flagged jobs: retry one from its last good
    state, or dismiss one a human judged not worth pursuing. Each is one tap
    and one gateway call; anything more belongs in the web UI."""

    def __init__(self, client: OrchestratorClient, failed_jobs: list[JobView]) -> None:
        super().__init__()
        self._client = client
        self._jobs = {j.id: j for j in failed_jobs}

        self.select = self._menu(_RETRY_PLACEHOLDER, failed_jobs)
        self.select.callback = self._on_retry
        self.add_item(self.select)

        self.dismiss_select = self._menu(_DISMISS_PLACEHOLDER, failed_jobs)
        self.dismiss_select.callback = self._on_dismiss
        self.add_item(self.dismiss_select)

    @staticmethod
    def _menu(placeholder: str, jobs: list[JobView]) -> discord.ui.Select:
        options = [
            discord.SelectOption(
                label=(j.resolved_title or j.release_name or j.id)[
                    :DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH
                ],
                value=j.id,
                description=(j.last_error or "")[:DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH],
            )
            for j in jobs
        ]
        return discord.ui.Select(placeholder=placeholder, options=options)

    async def _on_retry(self, interaction: discord.Interaction) -> None:
        await self._act(interaction, self._client.retry_job, "Retry", "Retried")

    async def _on_dismiss(self, interaction: discord.Interaction) -> None:
        await self._act(interaction, self._client.dismiss_job, "Dismiss", "Dismissed")

    @staticmethod
    async def _act(
        interaction: discord.Interaction, action: JobAction, verb: str, past: str
    ) -> None:
        try:
            job_id = interaction.data["values"][0]
        except (KeyError, IndexError):
            await interaction.response.send_message(_SELECTION_ERROR, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        job = await action(job_id)
        if job is None:
            await interaction.followup.send(f"{verb} request failed.", ephemeral=True)
            return

        await interaction.followup.send(
            f"{past} job `{job_id}` - now **{job.status}**.",
            ephemeral=True,
        )
