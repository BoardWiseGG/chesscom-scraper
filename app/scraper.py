import os
from typing import List, Tuple, Union

import aiohttp

from app.repo import Repo


class BaseScraper(Repo):
    def __init__(self, site: str, session: aiohttp.ClientSession):
        """Initialize a new web scraper.

        @param site:
            The site we are making requests out to.
        @param session:
            The `aiohttp.ClientSession` context our requests are made from.
        """
        super().__init__(site)
        self.session = session

    async def download_usernames(self) -> List[str]:
        """Collect all coach usernames from the specified site."""
        raise NotImplementedError()

    async def download_profile(self, username: str):
        """For each coach, download coach-specific data."""
        raise NotImplementedError()

    async def request(self, url: str) -> Tuple[Union[str, None], int]:
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

    async def scrape(self) -> List[str]:
        """Main entrypoint for scraping and exporting downloaded content.

        A `Scraper` is structured to operates in the following stages:

        1. Collect all coach usernames from the specified site.
        2. For each coach, download coach-specific data.
        3. Transform this data and export into uniform format.
        """
        os.makedirs(self.path_coaches_dir(), exist_ok=True)
        os.makedirs(self.path_pages_dir(), exist_ok=True)
        usernames = await self.download_usernames()
        for username in usernames:
            os.makedirs(self.path_coach_dir(username), exist_ok=True)
            await self.download_profile(username)

        return usernames
