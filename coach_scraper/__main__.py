import argparse
import asyncio
from dataclasses import dataclass
from typing import List

import aiohttp
import psycopg2
from lingua import LanguageDetector, LanguageDetectorBuilder

from coach_scraper.chesscom import Pipeline as ChesscomPipeline
from coach_scraper.database import backup_database, load_languages
from coach_scraper.lichess import Pipeline as LichessPipeline
from coach_scraper.types import Site


@dataclass
class Context:
    conn: psycopg2._psycopg.connection
    detector: LanguageDetector
    worker_count: int
    user_agent: str


async def _process(
    site: Site,
    context: Context,
    session: aiohttp.ClientSession,
):
    if site == Site.CHESSCOM:
        await ChesscomPipeline(worker_count=context.worker_count).process(
            context.conn, context.detector, session
        )
    elif site == Site.LICHESS:
        await LichessPipeline(worker_count=context.worker_count).process(
            context.conn, context.detector, session
        )
    else:
        assert False, f"Encountered unknown site: {site}."


async def _entrypoint(context: Context, sites: List[Site]):
    """Top-level entrypoint that dispatches a pipeline per requested site."""
    async with aiohttp.ClientSession(
        headers={"User-Agent": f"BoardWise coach-scraper ({context.user_agent})"}
    ) as session:
        await asyncio.gather(*[_process(site, context, session) for site in sites])


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

    # Other.
    parser.add_argument("--workers", type=int, default=5)

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
                Context(
                    conn=conn,
                    detector=detector,
                    user_agent=args.user_agent,
                    worker_count=args.workers,
                ),
                sites=list(map(Site, set(args.site))),
            )
        )
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
