import argparse
import asyncio
import csv
import json

import aiohttp

from app.chesscom import Exporter as ChesscomExporter
from app.chesscom import Scraper as ChesscomScraper
from app.lichess import Exporter as LichessExporter
from app.lichess import Scraper as LichessScraper
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
        action="append",
        choices=[
            Site.CHESSCOM.value,
            Site.LICHESS.value,
        ],
    )
    args = parser.parse_args()

    async with aiohttp.ClientSession(
        headers={"User-Agent": f"BoardWise coach-scraper ({args.user_agent})"}
    ) as session:
        with open("data/export.csv", "w") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            for site in set(args.site):
                scraper, exporter_cls = None, None

                if site == Site.CHESSCOM.value:
                    scraper = ChesscomScraper(session)
                    exporter_cls = ChesscomExporter
                elif site == Site.LICHESS.value:
                    scraper = LichessScraper(session)
                    exporter_cls = LichessExporter

                usernames = await scraper.scrape()
                for username in usernames:
                    export = exporter_cls(username).export()
                    writer.writerow(
                        [
                            # This should match the order data is loaded in the
                            # sql/export.sql script.
                            export["site"],
                            export["username"],
                            export.get("name", ""),
                            export.get("image_url", ""),
                            export.get("rapid", ""),
                            export.get("blitz", ""),
                            export.get("bullet", ""),
                        ]
                    )


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
