import argparse
import asyncio
from typing import List

import aiohttp
import psycopg2
from lingua import LanguageDetector, LanguageDetectorBuilder

from coach_scraper.chesscom import Pipeline as ChesscomPipeline
from coach_scraper.database import backup_database, load_languages
from coach_scraper.lichess import Pipeline as LichessPipeline
from coach_scraper.types import Site

# The number of parallel extraction jobs that are run at a time.
WORKER_COUNT = 10


async def _process(
    site: Site, conn, detector: LanguageDetector, session: aiohttp.ClientSession
):
    if site == Site.CHESSCOM:
        await ChesscomPipeline(worker_count=WORKER_COUNT).process(
            conn, detector, session
        )
    elif site == Site.LICHESS:
        await LichessPipeline(worker_count=WORKER_COUNT).process(
            conn, detector, session
        )
    else:
        assert False, f"Encountered unknown site: {site}."


async def _entrypoint(
    conn, detector: LanguageDetector, user_agent: str, sites: List[Site]
):
    """Top-level entrypoint that dispatches a pipeline per requested site."""
    async with aiohttp.ClientSession(
        headers={"User-Agent": f"BoardWise coach-scraper ({user_agent})"}
    ) as session:
        await asyncio.gather(
            *[_process(site, conn, detector, session) for site in sites]
        )


def main():
    parser = argparse.ArgumentParser(
        prog="coach-scraper",
        description="Scraping/exporting of chess coaches.",
    )

    # Database-related arguments.
    parser.add_argument("--host", required=True)
    parser.add_argument("--dbname", default="postgres")
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--password", default="password")
    parser.add_argument("--port", default=5432)

    # Client session-related arguments.
    parser.add_argument("--user-agent", required=True)
    parser.add_argument(
        "--site",
        required=True,
        action="append",
        choices=[
            Site.CHESSCOM.value,
            Site.LICHESS.value,
        ],
    )

    args = parser.parse_args()

    detector = LanguageDetectorBuilder.from_all_languages().build()

    conn = None
    try:
        conn = psycopg2.connect(
            dbname=args.dbname,
            user=args.user,
            host=args.host,
            password=args.password,
            port=args.port,
        )
        backup_database(conn)
        load_languages(conn)
        asyncio.run(
            _entrypoint(
                conn=conn,
                detector=detector,
                user_agent=args.user_agent,
                sites=list(map(Site, set(args.site))),
            )
        )
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
