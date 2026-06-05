import discord

from medialab_bot.client import TorrentDownloaderClient
from medialab_bot.constants import DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH
from medialab_bot.schemas.torrents import TorrentResult


class TorrentSelectMenu(discord.ui.View):
    def __init__(
        self,
        groups: dict[str, list[TorrentResult]],
        client: TorrentDownloaderClient,
        results_per_resolution: int,
    ) -> None:
        super().__init__()
        self._client = client
        self._indexed: dict[str, TorrentResult] = {}

        options: list[discord.SelectOption] = []
        for resolution, results in groups.items():
            top = sorted(results, key=lambda r: max(0, r.nbSeeders), reverse=True)[:results_per_resolution]
            for i, result in enumerate(top):
                key = f"{resolution}:{i}"
                self._indexed[key] = result
                label = f"{resolution} - {result.fileName}"[:DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH]
                description = f"{result.nbSeeders} seeders"[:DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH]
                options.append(discord.SelectOption(label=label, value=key, description=description))

        if not options:
            raise ValueError("TorrentSelectMenu requires at least one result")

        self.select = discord.ui.Select(placeholder="Choose a torrent...", options=options)
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        try:
            key = interaction.data["values"][0]
            result = self._indexed[key]
        except (KeyError, IndexError, ValueError):
            await interaction.response.send_message(
                "Something went wrong with your selection. Please try again.",
                ephemeral=True,
            )
            return

        if not result.fileUrl.startswith("magnet:"):
            await interaction.response.send_message(
                "Invalid torrent link. Please try a different result.",
                ephemeral=True,
            )
            return

        response = await self._client.download(result.fileUrl)
        if response is None:
            await interaction.response.send_message(
                "Download request failed. Please try again.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Download started: **{result.fileName}**",
            ephemeral=True,
        )
