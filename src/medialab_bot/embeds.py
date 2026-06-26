import discord

from medialab_bot.schemas.jobs import JobsResponse
from medialab_bot.schemas.system import DiskUsageResponse
from medialab_bot.schemas.transfers import MergedTransfersResponse

_BYTES_PER_KB = 1024


def transfers_embed(response: MergedTransfersResponse) -> discord.Embed:
    embed = discord.Embed(title="Active Transfers", color=discord.Color.green())
    for t in response.transfers.data:
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
    return embed


def jobs_embed(response: JobsResponse) -> discord.Embed:
    embed = discord.Embed(title="Pipeline Jobs", color=discord.Color.gold())
    for job in response.jobs:
        title = job.resolved_title or job.release_name or job.torrent_hash
        line = f"**{job.status}**"
        if job.last_error:
            line += f" - {job.last_error}"
        embed.add_field(
            name=f"{title} ({job.media_type.value})",
            value=f"{line}\nhash `{job.torrent_hash}`",
            inline=False,
        )
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
