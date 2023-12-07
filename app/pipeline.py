import asyncio
import os.path
from typing import Any, List, Tuple

import aiohttp
from lingua import LanguageDetector

from app.database import Row, RowKey, upsert_row
from app.locale import Locale
from app.types import Site, Title


class Fetcher:
    """Download and cache files from the specified site.

    Each implementation of this class is responsible for rate-limiting requests.
    """

    def __init__(self, site: Site, session: aiohttp.ClientSession):
        self.site = site
        self.session = session
        self.has_made_request = False

        os.makedirs(self.path_coaches_dir(), exist_ok=True)
        os.makedirs(self.path_pages_dir(), exist_ok=True)

    def path_site_dir(self):
        return os.path.join("data", self.site.value)

    def path_site_file(self, filename: str):
        return os.path.join(self.path_site_dir(), filename)

    def path_coaches_dir(self):
        return os.path.join(self.path_site_dir(), "coaches")

    def path_coach_dir(self, username: str):
        return os.path.join(self.path_coaches_dir(), username)

    def path_coach_file(self, username: str, filename: str):
        return os.path.join(self.path_coach_dir(username), filename)

    def path_pages_dir(self):
        return os.path.join(self.path_site_dir(), "pages")

    def path_page_file(self, page_no: int):
        return os.path.join(self.path_pages_dir(), f"{page_no}.txt")

    async def fetch(self, url: str) -> Tuple[str | None, int]:
        """Make network requests using the internal session.

        @param url
            The URL to make a GET request to.
        @return
            Tuple containing the response body (if the request was successful)
            and status code.
        """
        self.has_made_request = True
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.text(), 200
        return None, response.status

    async def scrape_usernames(self, page_no: int) -> List[str] | None:
        """Source the specified site for all coach usernames.

        All pages should be downloaded at `self.path_page_file()`. Any cached
        file should be a plain `.txt` file containing one username per-line.

        @param page_no:
            How many times this function was invoked (1-indexed). Useful to
            paginate responses back out to the `Pipeline` this `Downloader`
            is embedded in.
        @return:
            A list of usernames. Should return an empty list if no more
            usernames are found. Can return `None` to indicate the specified
            page should be skipped.
        """
        raise NotImplementedError()

    async def _download_user_files(self, username: str) -> None:
        os.makedirs(self.path_coach_dir(username), exist_ok=True)
        await self.download_user_files(username)

    async def download_user_files(self, username: str) -> None:
        """Source the specified site for all user-specific files.

        What files are downloaded depends on the `Downloader` implementation.
        All files should be downloaded at `self.path_coach_file()`.
        """
        raise NotImplementedError()


def _insert(row: Row, key: RowKey, value: Any):
    if value is not None:
        row[key] = value


class Extractor:
    def __init__(self, fetcher: Fetcher, detector: LanguageDetector, username: str):
        self.fetcher = fetcher
        self.detector = detector
        self.username = username

    def get_name(self) -> str | None:
        raise NotImplementedError()

    def get_image_url(self) -> str | None:
        raise NotImplementedError()

    def get_title(self) -> Title | None:
        raise NotImplementedError()

    def get_languages(self) -> List[Locale] | None:
        raise NotImplementedError()

    def get_rapid(self) -> int | None:
        raise NotImplementedError()

    def get_blitz(self) -> int | None:
        raise NotImplementedError()

    def get_bullet(self) -> int | None:
        raise NotImplementedError()

    def extract(self) -> Row:
        """Extract a table row from the coach-specific downloads."""
        row: Row = {}

        _insert(row, "site", self.fetcher.site)
        _insert(row, "username", self.username)

        _insert(row, "name", self.get_name())
        _insert(row, "image_url", self.get_image_url())
        _insert(row, "title", self.get_title())
        _insert(row, "languages", self.get_languages())
        _insert(row, "rapid", self.get_rapid())
        _insert(row, "blitz", self.get_blitz())
        _insert(row, "bullet", self.get_bullet())

        return row


async def task_worker(name, queue):
    while True:
        conn, extractor = await queue.get()
        upsert_row(conn, extractor.extract())
        queue.task_done()


class Pipeline:
    """Site specific download and extraction pipeline.

    Performs downloads serially but processes data extraction from downloaded
    files concurrently.
    """

    def __init__(self, worker_count):
        self.worker_count = worker_count

    def get_fetcher(self, session: aiohttp.ClientSession) -> Fetcher:
        raise NotImplementedError()

    def get_extractor(
        self, fetcher: Fetcher, detector: LanguageDetector, username: str
    ) -> Extractor:
        raise NotImplementedError()

    async def process(
        self, conn, detector: LanguageDetector, session: aiohttp.ClientSession
    ):
        fetcher = self.get_fetcher(session)

        queue: asyncio.Queue = asyncio.Queue()

        # Create a batch of workers to process the jobs put into the queue.
        workers = []
        for i in range(self.worker_count):
            worker = asyncio.create_task(task_worker(f"worker-{i}", queue))
            workers.append(worker)

        # Begin downloading all coach usernames and files. The workers will
        # run concurrently to extract all the relvant information and write
        page_no = 1
        usernames: List[str] | None = [""]
        while usernames is None or len(usernames):
            usernames = await fetcher.scrape_usernames(page_no)
            page_no += 1
            for username in usernames or []:
                await fetcher._download_user_files(username)
                extractor = self.get_extractor(fetcher, detector, username)
                queue.put_nowait((conn, extractor))

        # Wait until the queue is fully processed.
        await queue.join()

        # We can now turn down the workers.
        for worker in workers:
            worker.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
