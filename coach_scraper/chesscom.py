import asyncio
import json
import os
import os.path
from typing import List

import aiohttp
from bs4 import BeautifulSoup, SoupStrainer, Tag
from lingua import LanguageDetector

from coach_scraper.locale import Locale, lang_to_locale
from coach_scraper.pipeline import Extractor as BaseExtractor
from coach_scraper.pipeline import Fetcher as BaseFetcher
from coach_scraper.pipeline import Pipeline as BasePipeline
from coach_scraper.types import Site, Title

# The number of coach listing pages we will at most iterate through. This number
# was determined by going to chess.com/coaches?sortBy=alphabetical&page=1 and
# traversing to the last page.
MAX_PAGES = 64

# How long to wait between a batch of network requests.
SLEEP_SECS = 3


class Fetcher(BaseFetcher):
    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(site=Site.CHESSCOM, session=session)

    async def scrape_usernames(self, page_no: int) -> List[str] | None:
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

        url = f"https://www.chess.com/coaches?sortBy=alphabetical&page={page_no}"
        response, status_code = await self.fetch(url)
        if response is None:
            return None  # Skips this page.

        usernames = []
        soup = BeautifulSoup(response, "lxml")
        members = soup.find_all("a", class_="members-categories-username")
        for member in members:
            href = member.get("href")
            username = href[len("https://www.chess.com/member/") :]
            usernames.append(username)

        # Cache results.
        with open(filepath, "w") as f:
            for username in usernames:
                f.write(f"{username}\n")

        return usernames

    async def download_user_files(self, username: str) -> None:
        maybe_download = [
            (
                f"https://www.chess.com/member/{username}",
                self.path_coach_file(username, f"{username}.html"),
            ),
            (
                f"https://www.chess.com/callback/member/stats/{username}",
                self.path_coach_file(username, "stats.json"),
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


def _profile_filter(elem: Tag | str | None, attrs={}) -> bool:
    for className in [
        "profile-header-info",
        "profile-card-info",
        "profile-about",
    ]:
        if className in attrs.get("class", ""):
            return True
    return False


class Extractor(BaseExtractor):
    def __init__(self, fetcher: BaseFetcher, detector: LanguageDetector, username: str):
        super().__init__(fetcher, detector, username)

        self.profile_soup = None
        try:
            filename = self.fetcher.path_coach_file(username, f"{username}.html")
            with open(filename, "r") as f:
                self.profile_soup = BeautifulSoup(
                    f.read(), "lxml", parse_only=SoupStrainer(_profile_filter)
                )
        except FileNotFoundError:
            pass

        self.stats_json = {}
        try:
            filename = self.fetcher.path_coach_file(username, "stats.json")
            with open(filename, "r") as f:
                for s in json.load(f).get("stats", []):
                    if "key" in s and "stats" in s:
                        self.stats_json[s["key"]] = s["stats"]
        except FileNotFoundError:
            pass

    def get_name(self) -> str | None:
        if self.profile_soup is None:
            return None
        name = self.profile_soup.find("div", class_="profile-card-name")
        if not isinstance(name, Tag):
            return None
        return name.get_text().strip()

    def get_image_url(self) -> str | None:
        if self.profile_soup is None:
            return None
        div = self.profile_soup.find("div", class_="profile-header-avatar")
        if not isinstance(div, Tag):
            return None
        img = div.find("img")
        if not isinstance(img, Tag):
            return None
        src = img.get("src", "")
        if not isinstance(src, str):
            return None
        if "images.chesscomfiles.com" not in src:
            return None
        return src

    def get_title(self) -> Title | None:
        if self.profile_soup is None:
            return None
        a = self.profile_soup.find("a", class_="profile-card-chesstitle")
        if not isinstance(a, Tag):
            return None
        title = a.get_text().strip()
        try:
            return Title(title)
        except ValueError:
            return None

    def get_languages(self) -> List[Locale] | None:
        if self.profile_soup is None:
            return None
        about = self.profile_soup.find("div", class_="profile-about")
        if not isinstance(about, Tag):
            return None
        detected = self.detector.detect_language_of(about.text)
        if detected is None:
            return None
        code = lang_to_locale.get(detected)
        if code is None:
            return None
        return [code]

    def get_rapid(self) -> int | None:
        return self.stats_json.get("rapid", {}).get("rating")

    def get_blitz(self) -> int | None:
        return self.stats_json.get("lightning", {}).get("rating")

    def get_bullet(self) -> int | None:
        return self.stats_json.get("bullet", {}).get("rating")


class Pipeline(BasePipeline):
    def get_fetcher(self, session: aiohttp.ClientSession):
        return Fetcher(session)

    def get_extractor(
        self, fetcher: BaseFetcher, detector: LanguageDetector, username: str
    ):
        return Extractor(fetcher, detector, username)
