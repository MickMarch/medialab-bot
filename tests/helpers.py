from unittest.mock import AsyncMock, MagicMock


def make_message_mock() -> MagicMock:
    message = MagicMock()
    message.edit = AsyncMock()
    return message


def make_interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock(return_value=make_message_mock())
    interaction.edit_original_response = AsyncMock()
    return interaction
