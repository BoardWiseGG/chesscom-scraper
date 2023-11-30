import aiohttp
import argparse
import asyncio

from app.chesscom import Scraper as ChesscomScraper
from app.lichess import Scraper as LichessScraper
from app.scraper import Site


async def run():
    parser = argparse.ArgumentParser(
        prog="coach-scraper",
        description="HTML scraping of chess.com coaches.",
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
        elif args.site == Site.LICHESS.value:
            scraper = LichessScraper(session)

        await scraper.scrape()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
