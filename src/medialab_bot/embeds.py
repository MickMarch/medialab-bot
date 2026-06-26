import discord

from medialab_bot.schemas.system import DiskUsageResponse
from medialab_bot.schemas.transfers import TransferInfoResponse


def transfers_embed(response: TransferInfoResponse) -> discord.Embed:
    embed = discord.Embed(title="Active Transfers", color=discord.Color.green())
    for t in response.data:
        dl = t.download_speed // 1024
        ul = t.upload_speed // 1024
        embed.add_field(
            name=t.name,
            value=(
                f"{t.progress * 100:.1f}% | {t.state} | "
                f"DL {dl} KB/s | UL {ul} KB/s | ETA {t.eta_seconds}s"
            ),
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
