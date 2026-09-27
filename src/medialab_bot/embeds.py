import discord
from medialab_contracts import PosterSize, poster_url

from medialab_bot.constants import DISCORD_EMBED_MAX_FIELDS
from medialab_bot.format import format_progress
from medialab_bot.schemas.jobs import JobsResponse
from medialab_bot.schemas.system import DiskUsageResponse
from medialab_bot.schemas.transfers import MergedTransfersResponse

_BYTES_PER_KB = 1024


def _cap_note(embed: discord.Embed, total: int, noun: str) -> None:
    """Discord rejects an embed with more than 25 fields outright, which left the
    command "thinking" forever; show the first 25 and say how many are hidden."""
    hidden = total - DISCORD_EMBED_MAX_FIELDS
    if hidden > 0:
        embed.set_footer(
            text=f"Showing {DISCORD_EMBED_MAX_FIELDS} of {total} {noun}; {hidden} more not shown."
        )


def transfers_embed(response: MergedTransfersResponse) -> discord.Embed:
    embed = discord.Embed(title="Active Transfers", color=discord.Color.green())
    transfers = response.transfers.data
    for t in transfers[:DISCORD_EMBED_MAX_FIELDS]:
        dl = t.download_speed // _BYTES_PER_KB
        ul = t.upload_speed // _BYTES_PER_KB
        embed.add_field(
            name=t.name,
            value=(
                f"{t.progress * 100:.1f}% | {t.state} | "
                f"DL {dl} KB/s | UL {ul} KB/s | ETA {t.eta_seconds}s"
            ),
            inline=False,
        )
    _cap_note(embed, len(transfers), "transfers")
    return embed


def jobs_embed(response: JobsResponse) -> discord.Embed:
    embed = discord.Embed(title="Pipeline Jobs", color=discord.Color.gold())
    for job in response.jobs[:DISCORD_EMBED_MAX_FIELDS]:
        title = job.resolved_title or job.release_name or job.torrent_hash
        line = f"**{job.status}**"
        if job.last_error:
            line += f" - {job.last_error}"
        if job.progress is not None:
            line += f"\n{format_progress(job.progress.progress, job.progress.eta_seconds)}"
        embed.add_field(
            name=f"{title} ({job.media_type.value})",
            value=f"{line}\nhash `{job.torrent_hash}`",
            inline=False,
        )
    _cap_note(embed, len(response.jobs), "jobs")
    return embed


def storage_embed(response: DiskUsageResponse) -> discord.Embed:
    embed = discord.Embed(title="Storage", color=discord.Color.blue())
    embed.add_field(name="Path", value=response.path, inline=False)
    embed.add_field(name="Total", value=f"{response.total_gb:.1f} GB", inline=True)
    embed.add_field(
        name="Used",
        value=f"{response.used_gb:.1f} GB ({response.used_percent:.1f}%)",
        inline=True,
    )
    embed.add_field(name="Free", value=f"{response.free_gb:.1f} GB", inline=True)
    return embed


def display_title(title: str, year: str | None) -> str:
    return f"{title} ({year})" if year else title


def title_embed(
    title: str,
    year: str | None,
    *,
    overview: str = "",
    poster_path: str | None = None,
    footer: str | None = None,
) -> discord.Embed:
    """One title's card; the poster is a thumbnail only when TMDB has one."""
    embed = discord.Embed(
        title=display_title(title, year), description=overview or None, color=discord.Color.teal()
    )
    thumbnail = poster_url(poster_path, PosterSize.THUMBNAIL)
    if thumbnail is not None:
        embed.set_thumbnail(url=thumbnail)
    if footer:
        embed.set_footer(text=footer)
    return embed


def title_list_embed(heading: str, lines: list[str]) -> discord.Embed:
    return discord.Embed(title=heading, description="\n".join(lines), color=discord.Color.teal())
