"""
SQLiteSession factory — creates or reuses a persistent conversation session.

The same session_id across runs gives all agents full conversation history,
so follow-up questions like "fix the first issue" work correctly.
"""

from agents import SQLiteSession
from .. import config


def get_session(
    session_id: str | None = None,
    db_path: str | None = None,
) -> SQLiteSession:
    """
    Return a SQLiteSession bound to the given session_id and db file.
    Creates the DB file automatically if it doesn't exist.

    Args:
        session_id: Unique identifier for this conversation thread.
                    Defaults to config.SESSION_ID.
        db_path:    Path to the SQLite file.
                    Defaults to config.DB_PATH.

    Returns:
        A SQLiteSession instance ready to be passed to Runner.run().
    """
    return SQLiteSession(
        session_id=session_id or config.SESSION_ID,
        db_path=db_path or config.DB_PATH,
    )
