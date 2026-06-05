from medialab_bot.client._base import _BaseClient
from medialab_bot.client._status import _StatusMixin
from medialab_bot.client._tmdb import _TmdbMixin
from medialab_bot.client._torrents import _TorrentsMixin


class TorrentDownloaderClient(_TmdbMixin, _TorrentsMixin, _StatusMixin, _BaseClient):
    pass
