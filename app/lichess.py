import aiohttp
import asyncio
import os
import os.path

from app.scraper import AnsiColor, BaseScraper, Export, Site
from bs4 import BeautifulSoup
from typing import List


# The number of pages we will at most iterate through. This number was
# determined by going to https://lichess.org/coach/all/all/alphabetical
# and traversing to the last page.
MAX_PAGES = 162

# How long to wait between each network request.
SLEEP_SECS = 5


class Scraper(BaseScraper):
    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(site=Site.LICHESS.value, session=session)

    async def download_usernames(self) -> List[str]:
        """Scan through lichess.org/coach for all coaches' usernames.

        @return
            The complete list of scraped usernames across every coach listing
            page.
        """
        usernames = []
        for page_no in range(1, MAX_PAGES + 1):
            filepath = self.path_page_file(page_no)
            try:
                with open(filepath, "r") as f:
                    self.log(
                        [
                            (AnsiColor.INFO, "[INFO]"),
                            (None, ": Reading file "),
                            (AnsiColor.DATA, filepath),
                        ]
                    )
                    usernames.extend([line.strip() for line in f.readlines()])
            except FileNotFoundError:
                page_usernames = await self._scrape_page(page_no)
                if not page_usernames:
                    self.log(
                        [
                            (AnsiColor.ERROR, "[ERROR]"),
                            (None, ": Could not scrape page "),
                            (AnsiColor.DATA, str(page_no)),
                        ]
                    )
                    continue
                with open(filepath, "w") as f:
                    for username in page_usernames:
                        f.write(f"{username}\n")
                usernames.extend(page_usernames)
                self.log(
                    [
                        (AnsiColor.INFO, "[INFO]"),
                        (None, ": Downloaded page "),
                        (AnsiColor.DATA, filepath),
                    ]
                )
                await asyncio.sleep(SLEEP_SECS)

        return usernames

    async def _scrape_page(self, page_no: int):
        """Scan through lichess.org/coach/.../?page=<n> for all coaches'
        usernames.

        @param page_no
            The page consisting of at most 10 coaches (at the time of writing)
            whose usernames are to be scraped.
        @return
            The list of scraped usernames on the specified coach listing page.
        """
        url = f"https://lichess.org/coach/all/all/alphabetical?page={page_no}"
        response, status_code = await self.request(url)
        if response is None:
            self.log(
                [
                    (AnsiColor.ERROR, "[ERROR]"),
                    (None, ": Received status "),
                    (AnsiColor.DATA, f"{status_code} "),
                    (None, "when downloading page "),
                    (AnsiColor.DATA, str(page_no)),
                ]
            )
            return

        usernames = []
        soup = BeautifulSoup(response, "html.parser")
        members = soup.find_all("article", class_="coach-widget")
        for member in members:
            anchor = member.find("a", class_="overlay")
            if anchor:
                href = anchor.get("href")
                username = href[len("/coach/") :]
                usernames.append(username)

        return usernames

    async def download_profile(self, username: str):
        """For each coach, download coach-specific data.

        @param username
            The coach username corresponding to the downloaded files.
        """
        filepath = self.path_coach_file(username, f"{username}.html")
        if os.path.isfile(filepath):
            return False

        response, _unused_status = await self.request(
            url=f"https://lichess.org/coach/{username}"
        )
        if response is not None:
            with open(filepath, "w") as f:
                f.write(response)

        return True

    async def export(self, username: str) -> Export:
        """Transform coach-specific data into uniform format."""
        export: Export = {
            "fide_rapid": None,
        }
        return export
