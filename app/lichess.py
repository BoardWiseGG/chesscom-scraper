import asyncio
import os
import os.path
from typing import List

import aiohttp
from bs4 import BeautifulSoup, SoupStrainer

from app.exporter import BaseExporter
from app.repo import AnsiColor, Site
from app.scraper import BaseScraper

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
        soup = BeautifulSoup(response, "lxml")
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
        used_network1 = await self._download_profile_file(
            url=f"https://lichess.org/coach/{username}",
            username=username,
            filename=self.path_coach_file(username, f"{username}.html"),
        )
        used_network2 = await self._download_profile_file(
            url=f"https://lichess.org/@/{username}",
            username=username,
            filename=self.path_coach_file(username, "stats.html"),
        )

        if any([used_network1, used_network2]):
            self.log(
                [
                    (AnsiColor.INFO, "[INFO]"),
                    (None, ": Downloaded data for coach "),
                    (AnsiColor.DATA, username),
                ]
            )
            await asyncio.sleep(SLEEP_SECS)
        else:
            self.log(
                [
                    (AnsiColor.INFO, "[INFO]"),
                    (None, ": Skipping download for coach "),
                    (AnsiColor.DATA, username),
                ]
            )

    async def _download_profile_file(self, url: str, username: str, filename: str):
        """Writes the contents of url into the specified file.

        @param url
            The URL of the file to download.
        @param username
            The coach username corresponding to the downloaded file.
        @param filename
            The output file to write the downloaded content to.
        @return:
            True if we make a network request. False otherwise.
        """
        if os.path.isfile(filename):
            return False

        response, _unused_status = await self.request(url)
        if response is not None:
            with open(filename, "w") as f:
                f.write(response)

        return True


def _stats_filter(elem, attrs):
    """Includes only relevant segments of the `stats.html` file."""
    if "sub-ratings" in attrs.get("class", ""):
        return True


class Exporter(BaseExporter):
    def __init__(self, username: str):
        super().__init__(site=Site.LICHESS.value, username=username)

        self.stats_soup = None
        try:
            with open(self.path_coach_file(username, "stats.html"), "r") as f:
                stats_strainer = SoupStrainer(_stats_filter)
                self.stats_soup = BeautifulSoup(
                    f.read(), "lxml", parse_only=stats_strainer
                )
        except FileNotFoundError:
            pass

    def export_rapid(self):
        return self._find_rating("rapid")

    def export_blitz(self):
        return self._find_rating("blitz")

    def export_bullet(self):
        return self._find_rating("bullet")

    def _find_rating(self, name):
        if self.stats_soup is None:
            return None

        anchor = self.stats_soup.find("a", href=f"/@/{self.username}/perf/{name}")
        if anchor is None:
            return None
        rating = anchor.find("rating")
        if rating is None:
            return None
        strong = rating.find("strong")
        if strong is None:
            return None
        value = strong.get_text()
        if value[-1] == "?":
            value = value[:-1]

        try:
            return int(value)
        except ValueError:
            return None
