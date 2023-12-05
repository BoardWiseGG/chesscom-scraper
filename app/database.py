import sys
from datetime import datetime

from typing_extensions import TypedDict

SCHEMA_NAME = "coach_export"
TABLE_NAME = "export"


class Row(TypedDict, total=False):
    """Representation of a row of the export table.

    The (site, username) make up a unique key for each coach.
    """

    # Website the given coach was sourced from.
    site: str
    # Username used on the source site.
    username: str
    # Real name.
    name: str
    # Profile image used on the source site.
    image_url: str
    # Rapid rating relative to the site they were sourced from.
    rapid: int
    # Blitz rating relative to the site they were sourced from.
    blitz: int
    # Bullet rating relative to the site they were sourced from.
    bullet: int


def backup_database(conn):
    """Creates a backup of the export table.

    Simply copies the table at time of invocation into another table with a
    `_%t` suffix, where %t denotes the number of seconds since the Unix epoch.
    """
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = '{SCHEMA_NAME}'
            AND table_name = '{TABLE_NAME}';
            """
        )

        result = cursor.fetchone()
        if result is None:
            print(f"Missing `{SCHEMA_NAME}.{TABLE_NAME}` table.", file=sys.stderr)
            sys.exit(1)

        timestamp = int((datetime.now() - datetime(1970, 1, 1)).total_seconds())
        cursor.execute(
            f"""
            CREATE TABLE {SCHEMA_NAME}.{TABLE_NAME}_{timestamp}
            AS TABLE {SCHEMA_NAME}.{TABLE_NAME}
            """
        )
    finally:
        if cursor:
            cursor.close()
