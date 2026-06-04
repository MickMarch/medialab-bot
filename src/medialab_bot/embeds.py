import discord

from medialab_bot.schemas.tmdb import TmdbSearchResult


def search_results_embed(results: list[TmdbSearchResult]) -> discord.Embed:
    embed = discord.Embed(title="Search Results", color=discord.Color.blurple())
    for result in results:
        embed.add_field(
            name=f"{result.title} ({result.year}) [{result.media_type}]",
            value=f"⭐ {result.vote_average}",
            inline=False,
        )
    return embed
