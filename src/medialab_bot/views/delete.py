"""/delete: pick a job, see exactly what would be removed, confirm once."""

import discord

from medialab_bot.client import OrchestratorClient
from medialab_bot.constants import DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH
from medialab_bot.schemas.deletion import DeletionPlan
from medialab_bot.schemas.jobs import JobView

CONFIRM_TIMEOUT_SECONDS = 60.0
_MAX_LISTED_PATHS = 15
_DESCRIPTION_SEPARATOR = " · "
_DATE_LENGTH = len("YYYY-MM-DD")


def option_label(job: JobView) -> str:
    """``Title (Year)`` when resolved, else the release name, else the id."""
    if job.resolved_title:
        label = job.resolved_title
        if job.resolved_year:
            label = f"{label} ({job.resolved_year})"
    else:
        label = job.release_name or job.id
    return label[:DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH]


def option_description(job: JobView) -> str:
    """Status, date, then the release name: the only thing that tells two
    copies of one title apart (language, resolution, group)."""
    parts = [job.status, job.updated_at[:_DATE_LENGTH], job.release_name]
    return _DESCRIPTION_SEPARATOR.join(p for p in parts if p)[
        :DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH
    ]


def render_plan(plan: DeletionPlan) -> str:
    """The plan as the user must see it before confirming."""
    if plan.refused:
        return f"Cannot delete this job automatically: {plan.refused}"
    lines = [
        f"Nothing has happened yet. Pressing **Delete** below will remove, for job `{plan.job_id}`:"
    ]
    if plan.torrent:
        lines.append("- the torrent and its data in qBittorrent")
    if plan.download_folder:
        lines.append(f"- download folder `{plan.download_folder}` (if still present)")
    for path in plan.placed_paths[:_MAX_LISTED_PATHS]:
        lines.append(f"- `{path}`")
    hidden = len(plan.placed_paths) - _MAX_LISTED_PATHS
    if hidden > 0:
        lines.append(f"- and {hidden} more placed file(s)")
    if plan.scan_path:
        lines.append(f"- then tell Jellyfin `{plan.scan_path}` changed")
    if len(lines) == 1:
        lines.append("- nothing on disk; the job will just be marked deleted")
    return "\n".join(lines)


class DeleteConfirmView(discord.ui.View):
    """Red Delete plus Cancel, valid for a minute."""

    def __init__(self, client: OrchestratorClient, job_id: str) -> None:
        super().__init__(timeout=CONFIRM_TIMEOUT_SECONDS)
        self._client = client
        self._job_id = job_id

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)
        job = await self._client.delete_job(self._job_id)
        self.stop()
        if job is None:
            await interaction.followup.send("Delete failed; nothing was changed.", ephemeral=True)
            return
        await interaction.followup.send(
            f"Deleted job `{self._job_id}` - now **{job.status}**.", ephemeral=True
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.stop()
        await interaction.response.send_message("Cancelled; nothing was changed.", ephemeral=True)


class DeleteSelectView(discord.ui.View):
    """Pick the job to delete; the next message shows the plan and asks."""

    def __init__(self, client: OrchestratorClient, jobs: list[JobView]) -> None:
        super().__init__()
        self._client = client
        options = [
            discord.SelectOption(
                label=option_label(j), value=j.id, description=option_description(j)
            )
            for j in jobs
        ]
        self.select = discord.ui.Select(
            placeholder="Step 1 of 3: pick the download (release name shows language and quality)",
            options=options,
        )
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        try:
            job_id = interaction.data["values"][0]
        except (KeyError, IndexError):
            await interaction.response.send_message(
                "Something went wrong with your selection. Please try again.", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        plan = await self._client.deletion_plan(job_id)
        if plan is None:
            await interaction.followup.send("Could not fetch the deletion plan.", ephemeral=True)
            return
        kwargs: dict = {"content": render_plan(plan), "ephemeral": True}
        if not plan.refused:
            kwargs["view"] = DeleteConfirmView(self._client, job_id)
        await interaction.followup.send(**kwargs)
