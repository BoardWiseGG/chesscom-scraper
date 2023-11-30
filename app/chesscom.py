import aiohttp
import asyncio
import json
import os
import os.path

from app.scraper import AnsiColor, BaseScraper, Export, Site
from bs4 import BeautifulSoup
from typing import List


# The number of coach listing pages we will at most iterate through. This number
# was determined by going to chess.com/coaches?sortBy=alphabetical&page=1 and
# traversing to the last page.
MAX_PAGES = 64

# How long to wait between a batch of network requests.
SLEEP_SECS = 3


class Scraper(BaseScraper):
    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(site=Site.CHESSCOM.value, session=session)

    async def download_usernames(self) -> List[str]:
        """Scan through chess.com/coaches for all coaches' usernames.

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

    async def _scrape_page(self, page_no: int) -> List[str]:
        """Scan through chess.com/coaches/?page=<n> for all coaches' usernames.

        @param page_no
            The page consisting of at most 25 coaches (at the time of writing)
            whose usernames are to be scraped.
        @return
            The list of scraped usernames on the specified coach listing page.
        """
        url = f"https://www.chess.com/coaches?sortBy=alphabetical&page={page_no}"
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
        members = soup.find_all("a", class_="members-categories-username")
        for member in members:
            href = member.get("href")
            username = href[len("https://www.chess.com/member/") :]
            usernames.append(username)

        return usernames

    async def download_profile(self, username: str):
        """For each coach, download coach-specific data.

        This sends three parallel requests for:
        * the coach's profile,
        * the coach's recent activity,
        * the coach's stats.

        @param username
            The coach username corresponding to the downloaded files.
        """
        used_network = await asyncio.gather(
            self._download_profile_file(
                url=f"https://www.chess.com/member/{username}",
                username=username,
                filename=self.path_coach_file(username, f"{username}.html"),
            ),
            self._download_profile_file(
                url=f"https://www.chess.com/callback/member/activity/{username}?page=1",
                username=username,
                filename=self.path_coach_file(username, "activity.json"),
            ),
            self._download_profile_file(
                url=f"https://www.chess.com/callback/member/stats/{username}",
                username=username,
                filename=self.path_coach_file(username, "stats.json"),
            ),
        )
        if any(used_network):
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

    def _load_stats_json(self, stats: dict) -> Export:
        """Extract relevant fields from a `stats.json` file."""
        export: Export = {}
        for stat in stats.get("stats", []):
            if stat["key"] == "rapid":
                export["fide_rapid"] = stat["stats"]["rating"]
        return export

    async def export(self, username: str) -> Export:
        """Transform coach-specific data into uniform format."""
        stat_export: Export = {}
        try:
            with open(self.path_coach_file(username, "stats.json"), "r") as f:
                stat_export = self._load_stats_json(json.load(f))
        except FileNotFoundError:
            pass

        export: Export = {
            "fide_rapid": None,
        }
        export.update(stat_export)
        return export
