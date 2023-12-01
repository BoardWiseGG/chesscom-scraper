import argparse
import asyncio
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
        for site in set(args.site):
            scraper, exporter_cls = None, None

            if site == Site.CHESSCOM.value:
                scraper = ChesscomScraper(session)
                exporter_cls = ChesscomExporter
            elif site == Site.LICHESS.value:
                scraper = LichessScraper(session)
                exporter_cls = LichessExporter

            # Write out each coach data into NDJSON file.
            dump = []
            usernames = await scraper.scrape()
            for username in usernames:
                export = exporter_cls(username).export()
                dump.append(f"{json.dumps(export)}\n")

            with open(scraper.path_site_file("export.json"), "w") as f:
                f.writelines(dump)


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
