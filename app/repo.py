import enum
import os
from typing import List, Tuple, Union


class AnsiColor(enum.Enum):
    ERROR = "\033[0;31m"
    INFO = "\033[0;34m"
    DATA = "\033[0;36m"
    RESET = "\033[0m"


class Repo:
    """Shared filesystem-related functionality."""

    def __init__(self, site: str):
        self.site = site

    def path_site_dir(self):
        """The root directory for all site-related files."""
        return os.path.join("data", self.site)

    def path_site_file(self, filename: str):
        """Path to a top-level site-related file."""
        return os.path.join(self.path_site_dir(), filename)

    def path_coaches_dir(self):
        """The root directory for all coach-related downloads."""
        return os.path.join(self.path_site_dir(), "coaches")

    def path_coach_dir(self, username: str):
        """The root directory for a specific coach's downloads."""
        return os.path.join(self.path_coaches_dir(), username)

    def path_coach_file(self, username: str, filename: str):
        """Path to a coach-specific file download."""
        return os.path.join(self.path_coach_dir(username), filename)

    def path_pages_dir(self):
        """The root directory for all username listing files."""
        return os.path.join(self.path_site_dir(), "pages")

    def path_page_file(self, page_no: int):
        """The root directory for usernames scraped from a single page."""
        return os.path.join(self.path_pages_dir(), f"{page_no}.txt")

    def log(self, msgs: List[Tuple[Union[AnsiColor, None], str]]):
        transformed = []
        for k, v in msgs:
            if k is None:
                transformed.append(v)
            else:
                transformed.append(f"{k.value}{v}{AnsiColor.RESET.value}")

        print("".join(transformed))
