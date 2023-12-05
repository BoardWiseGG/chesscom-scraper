import asyncio
import os
import os.path
from typing import List, Union

import aiohttp
from bs4 import BeautifulSoup, SoupStrainer

from app.pipeline import Extractor as BaseExtractor
from app.pipeline import Fetcher as BaseFetcher
from app.pipeline import Pipeline as BasePipeline
from app.pipeline import Site

# The number of pages we will at most iterate through. This number was
# determined by going to https://lichess.org/coach/all/all/alphabetical
# and traversing to the last page.
MAX_PAGES = 162

# How long to wait between each network request.
SLEEP_SECS = 5


class Fetcher(BaseFetcher):
    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(site=Site.LICHESS, session=session)

    async def scrape_usernames(self, page_no: int) -> List[str]:
        if page_no > MAX_PAGES:
            return []

        print(f"{self.site.value}: Scraping page {page_no}/{MAX_PAGES}")

        filepath = self.path_page_file(page_no)
        try:
            with open(filepath, "r") as f:
                return [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            pass

        if self.has_made_request:
            await asyncio.sleep(SLEEP_SECS)

        url = f"https://lichess.org/coach/all/all/alphabetical?page={page_no}"
        response, status_code = await self.fetch(url)
        if response is None:
            return None  # Skips this page.

        usernames = []
        soup = BeautifulSoup(response, "lxml")
        members = soup.find_all("article", class_="coach-widget")
        for member in members:
            a = member.find("a", class_="overlay")
            if a:
                href = a.get("href")
                username = href[len("/coach/") :]
                usernames.append(username)

        with open(filepath, "w") as f:
            for username in usernames:
                f.write(f"{username}\n")

        return usernames

    async def download_user_files(self, username: str) -> None:
        maybe_download = [
            (
                f"https://lichess.org/coach/{username}",
                self.path_coach_file(username, f"{username}.html"),
            ),
            (
                f"https://lichess.org/@/{username}",
                self.path_coach_file(username, "stats.html"),
            ),
        ]

        to_download = []
        for d_url, d_filename in maybe_download:
            if os.path.isfile(d_filename):
                continue
            to_download.append((d_url, d_filename))

        if not to_download:
            return

        if self.has_made_request:
            await asyncio.sleep(SLEEP_SECS)

        await asyncio.gather(
            *[self._download_file(url=d[0], filename=d[1]) for d in to_download]
        )

    async def _download_file(self, url: str, filename: str) -> None:
        response, _unused_status = await self.fetch(url)
        if response is not None:
            with open(filename, "w") as f:
                f.write(response)


def _profile_filter(elem, attrs):
    if "coach-widget" in attrs.get("class", ""):
        return True


def _stats_filter(elem, attrs):
    if "profile-side" in attrs.get("class", ""):
        return True
    if "sub-ratings" in attrs.get("class", ""):
        return True


class Extractor(BaseExtractor):
    def __init__(self, fetcher: Fetcher, username: str):
        super().__init__(fetcher, username)

        self.profile_soup = None
        try:
            filename = self.fetcher.path_coach_file(username, f"{username}.html")
            with open(filename, "r") as f:
                self.profile_soup = BeautifulSoup(
                    f.read(), "lxml", parse_only=SoupStrainer(_profile_filter)
                )
        except FileNotFoundError:
            pass

        self.stats_soup = None
        try:
            filename = self.fetcher.path_coach_file(username, "stats.html")
            with open(filename, "r") as f:
                self.stats_soup = BeautifulSoup(
                    f.read(), "lxml", parse_only=SoupStrainer(_stats_filter)
                )
        except FileNotFoundError:
            pass

    def get_name(self) -> Union[str, None]:
        try:
            profile_side = self.stats_soup.find("div", class_="profile-side")
            user_infos = profile_side.find("div", class_="user-infos")
            name = user_infos.find("strong", class_="name")
            return name.get_text().strip()
        except AttributeError:
            return None

    def get_image_url(self) -> Union[str, None]:
        try:
            picture = self.profile_soup.find("img", class_="picture")
            src = picture.get("src", "")
            if "image.lichess1.org" in src:
                return src
        except AttributeError:
            return None

    def get_rapid(self) -> Union[int, None]:
        return self._find_rating("rapid")

    def get_blitz(self) -> Union[int, None]:
        return self._find_rating("blitz")

    def get_bullet(self) -> Union[int, None]:
        return self._find_rating("bullet")

    def _find_rating(self, name) -> Union[int, None]:
        try:
            a = self.stats_soup.find("a", href=f"/@/{self.username}/perf/{name}")
            rating = a.find("rating")
            strong = rating.find("strong")
            value = strong.get_text()
            if value[-1] == "?":
                value = value[:-1]
            return int(value)
        except (AttributeError, ValueError):
            return None


class Pipeline(BasePipeline):
    def get_fetcher(self, session: aiohttp.ClientSession):
        return Fetcher(session)

    def get_extractor(self, fetcher: Fetcher, username: str):
        return Extractor(fetcher, username)
