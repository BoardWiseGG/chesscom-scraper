import aiohttp
import enum
import json
import os

from typing import List, Union
from typing_extensions import TypedDict


class Site(enum.Enum):
    CHESSCOM = "chesscom"
    LICHESS = "lichess"


Export = TypedDict(
    "Export",
    {
        "fide_rapid": Union[int, None],
    },
)


class BaseScraper:
    def __init__(self, site: str, session: aiohttp.ClientSession):
        """Initialize a new web scraper and exporter.

        @param site:
            The site we are making requests out to.
        @param session:
            The `aiohttp.ClientSession` context our requests are made from.
        """
        self.site = site
        self.session = session

    async def download_usernames(self) -> List[str]:
        """Collect all coach usernames from the specified site."""
        raise NotImplementedError()

    async def download_profile(self, username: str):
        """For each coach, download coach-specific data."""
        raise NotImplementedError()

    async def export(self, username: str) -> Export:
        """Transform coach-specific data into uniform format."""
        raise NotImplementedError()

    async def request(self, url: str) -> (Union[str, None], int):
        """Make network requests using the internal session.

        @param url
            The URL to make a GET request to.
        @return
            Tuple containing the response body (if the request was successful)
            and status code.
        """
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.text(), 200
        return None, response.status

    async def scrape(self):
        """Main entrypoint for scraping and exporting downloaded content.

        A `Scraper` is structured to operates in the following stages:

        1. Collect all coach usernames from the specified site.
        2. For each coach, download coach-specific data.
        3. Transform this data and export into uniform format.
        """
        os.makedirs(self.path_coaches_dir(), exist_ok=True)
        os.makedirs(self.path_pages_dir(), exist_ok=True)
        usernames = self.download_usernames()
        for username in usernames:
            os.makedirs(self.path_coach_dir(username), exist_ok=True)
            await self.download_profile(username)
            export = await self.export(username)
            with open(self.path_coach_file(username, "export.json")) as f:
                json.dump(export, f)

    def path_coaches_dir(self):
        """The root directory for all coach-related downloads."""
        return os.path.join("data", self.site, "coach")

    def path_coach_dir(self, username: str):
        """The root directory for a specific coach's downloads."""
        return os.path.join(self.path_coaches_dir(), username)

    def path_coach_file(self, username: str, filename: str):
        """Path to a coach-specific file download."""
        return os.path.join(self.path_coach_dir(username), filename)

    def path_pages_dir(self):
        """The root directory for all username listing files."""
        return os.path.join("data", self.site, "pages")

    def path_page_file(self, page_no: int):
        """The root directory for usernames scraped from a single page."""
        return os.path.join(self.path_pages_dir(), str(page_no))
