def iso_utc(dt):
    """
    Serialize a datetime to ISO format with an explicit UTC marker.

    The database driver (SQLite, and in some configurations MySQL too)
    strips timezone info on round-trip, so a naive datetime.isoformat()
    call produces a string with no offset (e.g. "2026-06-21T11:15:18").
    When the frontend parses that with `new Date(...)`, the browser
    assumes it's LOCAL time, not UTC - causing timestamps to appear
    hours off depending on the user's timezone.

    This helper guarantees the 'Z' suffix is always present so
    JavaScript's Date parser correctly interprets it as UTC.
    """
    if dt is None:
        return None
    # If the value is naive (no tzinfo), we know from our model defaults
    # that it was always written in UTC, so we just append the 'Z' marker
    # directly on the isoformat string rather than re-attaching tzinfo
    # (which would require importing datetime/timezone here unnecessarily).
    s = dt.isoformat()
    if dt.tzinfo is None:
        return s + 'Z'
    return s
