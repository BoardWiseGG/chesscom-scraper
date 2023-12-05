import asyncio
import enum
import os.path
from typing import Any, Union

import aiohttp

from app.database import Row


class Site(enum.Enum):
    CHESSCOM = "chesscom"
    LICHESS = "lichess"


class Fetcher:
    """Download and cache files from the specified site.

    Each implementation of this class is responsible for rate-limiting requests.
    """

    def __init__(self, site: str, session: aiohttp.ClientSession):
        self.site = site
        self.session = session

    def path_site_dir(self):
        return os.path.join("data", self.site)

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

    async def scrape_usernames(self, page_no: int):
        """Source the specified site for all coach usernames.

        All pages should be downloaded at `self.path_page_file()`. Any cached
        file should be a plain `.txt` file containing one username per-line.

        @param page_no:
            How many times this function was invoked (1-indexed). Useful to
            paginate responses back out to the `Pipeline` this `Downloader`
            is embedded in.
        @return:
            A list of usernames. Should return an empty list if no more
            usernames are found.
        """
        raise NotImplementedError()

    async def download_user_files(self, username: str):
        """Source the specified site for all user-specific files.

        What files are downloaded depends on the `Downloader` implementation.
        All files should be downloaded at `self.path_coach_file()`.
        """
        raise NotImplementedError()


def _insert(row: Row, key: str, value: Any):
    if value is not None:
        row[key] = value


class Extractor:
    def __init__(self, fetcher: Fetcher, username: str):
        self.fetcher = fetcher
        self.username = username

    def get_name(self) -> Union[str, None]:
        raise NotImplementedError()

    def get_image_url(self) -> Union[str, None]:
        raise NotImplementedError()

    def get_rapid(self) -> Union[int, None]:
        raise NotImplementedError()

    def get_blitz(self) -> Union[int, None]:
        raise NotImplementedError()

    def get_bullet(self) -> Union[int, None]:
        raise NotImplementedError()

    def extract(self) -> Row:
        """Extract a table row from the coach-specific downloads."""
        row: Row = {}

        _insert(row, "site", self.fetcher.site)
        _insert(row, "username", self.username)

        _insert(row, "name", self.get_name())
        _insert(row, "image_url", self.get_image_url())
        _insert(row, "rapid", self.get_rapid())
        _insert(row, "blitz", self.get_blitz())
        _insert(row, "bullet", self.get_bullet())

        return row


async def worker(name, queue):
    while True:
        conn, extractor = await queue.get()
        print(extractor.username)
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

    def get_extractor(self, fetcher: Fetcher, username: str) -> Extractor:
        raise NotImplementedError()

    async def process(self, conn, session: aiohttp.ClientSession):
        fetcher = self.get_fetcher(session)

        queue = asyncio.Queue()

        # Create a batch of workers to process the jobs put into the queue.
        tasks = []
        for i in range(self.worker_count):
            task = asyncio.create_task(worker(f"worker-{i}", queue))
            tasks.append(task)

        # Begin downloading all coach usernames and files. The workers will
        # run concurrently to extract all the relvant information and write
        page_no = 1
        usernames = [None]
        while len(usernames):
            usernames = await fetcher.scrape_usernames(page_no)
            for username in usernames:
                await fetcher.download_user_files(username)
                extractor = self.get_extractor(fetcher, username)
                queue.put_nowait((conn, extractor))
            page_no += 1

        # Wait until the queue is fully processed.
        await queue.join()

        # We can now turn down the workers.
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
