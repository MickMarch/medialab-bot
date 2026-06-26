from medialab_bot.client._jobs import _JobsMixin
from medialab_bot.client._status import _StatusMixin
from medialab_bot.client._tmdb import _TmdbMixin
from medialab_bot.client._torrents import _TorrentsMixin


class OrchestratorClient(_TmdbMixin, _TorrentsMixin, _StatusMixin, _JobsMixin):
    """The bot's single downstream dependency: the medialab-orchestrator gateway."""
