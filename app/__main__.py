import aiohttp
import argparse
import asyncio
import json

from app.chesscom import (
    Exporter as ChesscomExporter,
    Scraper as ChesscomScraper,
)
from app.lichess import (
    Exporter as LichessExporter,
    Scraper as LichessScraper,
)
from app.repo import Site


async def run():
    parser = argparse.ArgumentParser(
        prog="coach-scraper",
        description="Scraping/exporting of chess coaches.",
    )
    parser.add_argument("-u", "--user-agent", required=True)
    parser.add_argument(
        "-s",
        "--site",
        required=True,
        choices=[
            Site.CHESSCOM.value,
            Site.LICHESS.value,
        ],
    )
    args = parser.parse_args()

    async with aiohttp.ClientSession(
        headers={"User-Agent": f"BoardWise coach-scraper ({args.user_agent})"}
    ) as session:
        if args.site == Site.CHESSCOM.value:
            scraper = ChesscomScraper(session)
            exporter_cls = ChesscomExporter
        elif args.site == Site.LICHESS.value:
            scraper = LichessScraper(session)
            exporter_cls = LichessExporter

        dump = {}

        usernames = await scraper.scrape()
        for username in usernames:
            dump[username] = exporter_cls(username).export()

        with open(scraper.path_site_file("export.json"), "w") as f:
            json.dump(dump, f, indent=2)


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
