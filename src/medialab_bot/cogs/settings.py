"""/settings: view, override and reset the suite's runtime settings.

The gateway owns validation and persistence; the bot renders and relays.
Spec: docs/specs/runtime-settings.md in the workspace.
"""

import discord
from discord import app_commands
from discord.ext import commands
from medialab_contracts import SettingView

from medialab_bot.client import OrchestratorClient
from medialab_bot.constants import DISCORD_AUTOCOMPLETE_MAX_CHOICES
from medialab_bot.embeds import settings_embed

SETTINGS_FETCH_FAILED_MESSAGE = "Failed to fetch settings."


def _applied(service: str, view: SettingView, verb: str) -> str:
    return f"`{view.key}` on `{service}` {verb} **{view.value}**. Applies: {view.applies}."


def _refused(service: str, key: str, verb: str) -> str:
    return (
        f"`{key}` on `{service}` was not {verb}: unknown service or key, "
        "or the value is out of bounds."
    )


class SettingsCog(commands.Cog):
    settings = app_commands.Group(name="settings", description="Suite runtime settings")

    def __init__(self, client: OrchestratorClient) -> None:
        self._client = client

    @settings.command(name="show", description="Every service's settings and their values")
    async def show(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        response = await self._client.get_settings()
        if response is None:
            await interaction.followup.send(SETTINGS_FETCH_FAILED_MESSAGE, ephemeral=True)
            return
        await interaction.followup.send(embed=settings_embed(response), ephemeral=True)

    @settings.command(name="set", description="Override one setting")
    @app_commands.describe(
        service="Service that owns the setting", key="Setting", value="New value"
    )
    async def set(
        self, interaction: discord.Interaction, service: str, key: str, value: str
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        view = await self._client.set_setting(service, key, value)
        if view is None:
            await interaction.followup.send(_refused(service, key, "changed"), ephemeral=True)
            return
        await interaction.followup.send(_applied(service, view, "set to"), ephemeral=True)

    @settings.command(
        name="reset", description="Drop an override; back to the .env or default value"
    )
    @app_commands.describe(service="Service that owns the setting", key="Setting")
    async def reset(self, interaction: discord.Interaction, service: str, key: str) -> None:
        await interaction.response.defer(ephemeral=True)
        view = await self._client.reset_setting(service, key)
        if view is None:
            await interaction.followup.send(_refused(service, key, "reset"), ephemeral=True)
            return
        await interaction.followup.send(_applied(service, view, "reset to"), ephemeral=True)

    @set.autocomplete("service")
    @reset.autocomplete("service")
    async def service_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        response = await self._client.get_settings()
        if response is None:
            return []
        typed = current.lower()
        return [
            app_commands.Choice(name=service, value=service)
            for service in response.services
            if typed in service.lower()
        ][:DISCORD_AUTOCOMPLETE_MAX_CHOICES]

    @set.autocomplete("key")
    @reset.autocomplete("key")
    async def key_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Keys of the chosen service; every service's keys before one is chosen."""
        response = await self._client.get_settings()
        if response is None:
            return []
        chosen = getattr(interaction.namespace, "service", None)
        services = [chosen] if chosen in response.services else list(response.services)
        typed = current.lower()
        return [
            app_commands.Choice(name=view.key, value=view.key)
            for service in services
            for view in response.services[service]
            if typed in view.key.lower()
        ][:DISCORD_AUTOCOMPLETE_MAX_CHOICES]
