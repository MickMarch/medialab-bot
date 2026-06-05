import discord

from medialab_bot.schemas.system import StorageResponse
from medialab_bot.schemas.tmdb import TmdbSearchResult
from medialab_bot.schemas.transfers import TransferInfoResponse


def search_results_embed(results: list[TmdbSearchResult]) -> discord.Embed:
    embed = discord.Embed(title="Search Results", color=discord.Color.blurple())
    for result in results:
        embed.add_field(
            name=f"{result.title} ({result.year}) [{result.media_type}]",
            value=f"⭐ {result.vote_average}",
            inline=False,
        )
    return embed


def transfers_embed(response: TransferInfoResponse) -> discord.Embed:
    embed = discord.Embed(title="Active Transfers", color=discord.Color.green())
    for t in response.data:
        dl = t.download_speed // 1024
        ul = t.upload_speed // 1024
        embed.add_field(
            name=t.name,
            value=f"{t.progress * 100:.1f}% | {t.state} | DL {dl} KB/s | UL {ul} KB/s | ETA {t.eta_seconds}s",
            inline=False,
        )
    return embed


def storage_embed(response: StorageResponse) -> discord.Embed:
    d = response.data
    embed = discord.Embed(title="Storage", color=discord.Color.blue())
    embed.add_field(name="Path", value=d.path, inline=False)
    embed.add_field(name="Total", value=f"{d.total_gb:.1f} GB", inline=True)
    embed.add_field(name="Used", value=f"{d.used_gb:.1f} GB ({d.used_percent:.1f}%)", inline=True)
    embed.add_field(name="Free", value=f"{d.free_gb:.1f} GB", inline=True)
    return embed
