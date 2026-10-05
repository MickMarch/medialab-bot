from medialab_contracts import WatchlistKind

DISCORD_SELECT_OPTION_MAX_LABEL_LENGTH = 100
DISCORD_SELECT_MAX_OPTIONS = 25
DISCORD_EMBED_MAX_FIELDS = 25
DISCORD_AUTOCOMPLETE_MAX_CHOICES = 25

# Gateway error codes whose detail is shown as-is: the request was fine and a
# retry may succeed. Every other code keeps the generic message.
SOURCE_UNREACHABLE_CODE = "SOURCE_UNREACHABLE"
TMDB_UNAVAILABLE_CODE = "TMDB_UNAVAILABLE"
RETRYABLE_ERROR_CODES = frozenset({SOURCE_UNREACHABLE_CODE, TMDB_UNAVAILABLE_CODE})

IN_LIBRARY_MARKER = "in Jellyfin"
SAVED_MARKER = "saved"
FOLLOWING_MARKER = "following"
WATCHLIST_MARKERS = {
    WatchlistKind.SAVED: SAVED_MARKER,
    WatchlistKind.FOLLOWING: FOLLOWING_MARKER,
}
