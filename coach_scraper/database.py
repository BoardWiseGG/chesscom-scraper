import random
import sys
from datetime import datetime
from typing import List, Literal

import psycopg2
from typing_extensions import TypedDict

from coach_scraper.locale import Locale, locale_to_str, native_to_locale
from coach_scraper.types import Site, Title

SCHEMA_NAME = "coach_scraper"
MAIN_TABLE_NAME = "export"
LANG_TABLE_NAME = "languages"


RowKey = (
    Literal["site"]
    | Literal["username"]
    | Literal["name"]
    | Literal["image_url"]
    | Literal["title"]
    | Literal["languages"]
    | Literal["rapid"]
    | Literal["blitz"]
    | Literal["bullet"]
)


class Row(TypedDict, total=False):
    """Representation of a row of the export table.

    The (site, username) make up a unique key for each coach.
    """

    # Website the given coach was sourced from.
    site: Site
    # Username used on the source site.
    username: str
    # Real name.
    name: str
    # Profile image used on the source site.
    image_url: str
    # The FIDE title assigned to the coach on the source siste.
    title: Title
    # The list of languages the coach is fluent in.
    languages: List[Locale]
    # Rapid rating relative to the site they were sourced from.
    rapid: int
    # Blitz rating relative to the site they were sourced from.
    blitz: int
    # Bullet rating relative to the site they were sourced from.
    bullet: int


def load_languages(conn: psycopg2._psycopg.connection):
    """Load all known languages into the languages table."""
    cursor = None
    try:
        cursor = conn.cursor()
        for pos, (name, loc) in enumerate(list(native_to_locale.items())):
            cursor.execute(
                f"""
                INSERT INTO {SCHEMA_NAME}.{LANG_TABLE_NAME}
                  (code, name, pos)
                VALUES
                  (%s, %s, %s)
                ON CONFLICT
                  (code)
                DO UPDATE SET
                  name = EXCLUDED.name;
                """,
                [locale_to_str(loc), name, pos],
            )
        conn.commit()
    finally:
        if cursor:
            cursor.close()


def backup_database(conn: psycopg2._psycopg.connection):
    """Creates a backup of the export table.

    Simply copies the table at time of invocation into another table with a
    `_%t` suffix, where %t denotes the number of seconds since the Unix epoch.
    """
    cursor = None
    try:
        cursor = conn.cursor()
        timestamp = int((datetime.now() - datetime(1970, 1, 1)).total_seconds())
        for table_name in [MAIN_TABLE_NAME, LANG_TABLE_NAME]:
            cursor.execute(
                f"""
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = '{SCHEMA_NAME}'
                AND table_name = '{table_name}';
                """
            )

            result = cursor.fetchone()
            if result is None:
                print(f"Missing `{SCHEMA_NAME}.{table_name}` table.", file=sys.stderr)
                sys.exit(1)

            cursor.execute(
                f"""
                CREATE TABLE {SCHEMA_NAME}.{table_name}_{timestamp}
                AS TABLE {SCHEMA_NAME}.{table_name}
                """
            )
    finally:
        if cursor:
            cursor.close()


def upsert_row(conn: psycopg2._psycopg.connection, row: Row):
    """Upsert the specified `Row` into the database table."""
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {SCHEMA_NAME}.{MAIN_TABLE_NAME}
              ( site
              , username
              , name
              , image_url
              , title
              , languages
              , rapid
              , blitz
              , bullet
              , position
              )
            VALUES
              ( %s
              , %s
              , %s
              , %s
              , %s
              , %s
              , %s
              , %s
              , %s
              , %s
              )
            ON CONFLICT
              (site, username)
            DO UPDATE SET
              name = EXCLUDED.name,
              image_url = EXCLUDED.image_url,
              title = EXCLUDED.title,
              languages = EXCLUDED.languages,
              rapid = EXCLUDED.rapid,
              blitz = EXCLUDED.blitz,
              bullet = EXCLUDED.bullet,
              position = EXCLUDED.position;
            """,
            [
                row["site"].value,
                row["username"],
                row.get("name"),
                row.get("image_url"),
                row["title"].value if "title" in row else None,
                list(map(locale_to_str, row.get("languages", []))),
                row.get("rapid"),
                row.get("blitz"),
                row.get("bullet"),
                random.randint(0, 1000000),
            ],
        )
        conn.commit()
    finally:
        if cursor:
            cursor.close()
