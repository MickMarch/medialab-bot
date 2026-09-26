import discord

from medialab_bot.constants import DISCORD_EMBED_MAX_FIELDS
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
