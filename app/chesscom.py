import aiohttp
import argparse
import asyncio
import json
import os
import os.path

from bs4 import BeautifulSoup
from typing import List


# The root directory containing downloaded files for a coach.
DATA_COACH_DIR = "data/coach/{username}"

# Raw HTML of coach profile page.
DATA_COACH_PROFILE = "data/coach/{username}/{username}.html"

# Raw JSON of recent coach activity.
DATA_COACH_ACTIVITY = "data/coach/{username}/activity.json"

# Raw JSON of profile-visible coach statistics.
DATA_COACH_STATS = "data/coach/{username}/stats.json"

# The processed collection of stats, aggregated from the other files.
DATA_COACH_EXPORT = "data/coach/{username}/export.json"

# Where a part of all discovered coach usernames is stored.
DATA_COACH_LIST = "data/pages/{page_no}.txt"

# The "User-Agent" value set in every request to chess.com.
USER_AGENT = "BoardWise chesscom-scraper ({user_agent})"

# How long to wait between a batch of network requests.
SLEEP_SECS = 3


def ANSI_COLOR(s: str):
    """Print colored output to the console."""
    return f"\033[0;34m{s}\033[0m"  # Blue


async def chesscom_request(session: aiohttp.ClientSession, url: str):
    """Convenience function for network requests to chess.com.

    @param session
        The `aiohttp.ClientSession` context our requests are made from.
    @param url
        The URL to send a request to.
    @return
        The text response returned by the server at @url.
    """
    async with session.get(url) as response:
        if response.status == 200:
            return await response.text()
        print(f"Encountered {response.status} when retrieving {url}.")


async def _scrape_page_coach_usernames(session: aiohttp.ClientSession, page_no: int):
    """Scan through chess.com/coaches/?page=<n> for all coaches' usernames.

    @param session
        The `aiohttp.ClientSession` context our requests are made from.
    @param page_no
        The page consisting of at most 25 coaches (at the time of writing)
        whose usernames are to be scraped.
    @return
        The list of scraped usernames on the specified coach listing page.
    """
    url = f"https://www.chess.com/coaches?sortBy=alphabetical&page={page_no}"
    response = await chesscom_request(session, url)
    if response is None:
        return

    usernames = []
    soup = BeautifulSoup(response, "html.parser")
    members = soup.find_all("a", class_="members-categories-username")
    for member in members:
        href = member.get("href")
        username = href[len("https://www.chess.com/member/") :]
        usernames.append(username)

    return usernames


async def _scrape_all_coach_usernames(
    session: aiohttp.ClientSession, max_pages: int = 64
):
    """Scan through chess.com/coaches for all coaches' usernames.

    @param session
        The `aiohttp.ClientSession` context our requests are made from.
    @param max_pages
        The number of pages we will at most iterate through. This number was
        determined by going to chess.com/coaches?sortBy=alphabetical&page=1
        and traversing to the last page.
    @return
        The complete list of scraped usernames across every coach listing page.
    """
    usernames = []
    for page_no in range(1, max_pages + 1):
        filepath = DATA_COACH_LIST.format(page_no=page_no)
        try:
            with open(filepath, "r") as f:
                usernames.extend(f.readlines())
            print(f"Skipping {ANSI_COLOR(filepath)}")
        except FileNotFoundError:
            page_usernames = await _scrape_page_coach_usernames(session, page_no)
            if not page_usernames:
                print(f"Could not write {ANSI_COLOR(filepath)}")
                continue
            with open(filepath, "w") as f:
                for username in page_usernames:
                    f.write(f"{username}\n")
            usernames.extend(page_usernames)
            print(f"Downloaded {ANSI_COLOR(filepath)}")
            await asyncio.sleep(SLEEP_SECS)

    return usernames


async def _download_coach_file(
    session: aiohttp.ClientSession, url: str, username: str, filename: str
):
    """Writes the contents of @url into `DATA_COACH_FILE`.

    @param session
        The `aiohttp.ClientSession` context our requests are made from.
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

    response = await chesscom_request(session, url)
    if response is not None:
        with open(filename, "w") as f:
            f.write(response)
    return True


async def _download_coach_data(session: aiohttp.ClientSession, username: str):
    """Download coach-related data to the `DATA_COACH_DIR` directory.

    This sends three parallel requests for:
    * the coach's profile,
    * the coach's recent activity,
    * the coach's stats.

    @param session
        The `aiohttp.ClientSession` context our requests are made from.
    @param username
        The coach username corresponding to the downloaded files.
    """
    used_network = await asyncio.gather(
        _download_coach_file(
            session,
            url=f"https://www.chess.com/member/{username}",
            username=username,
            filename=DATA_COACH_PROFILE.format(username=username),
        ),
        _download_coach_file(
            session,
            url=f"https://www.chess.com/callback/member/activity/{username}?page=1",
            username=username,
            filename=DATA_COACH_ACTIVITY.format(username=username),
        ),
        _download_coach_file(
            session,
            url=f"https://www.chess.com/callback/member/stats/{username}",
            username=username,
            filename=DATA_COACH_STATS.format(username=username),
        ),
    )
    if any(used_network):
        print(f"Downloaded {ANSI_COLOR(username)}")
        await asyncio.sleep(SLEEP_SECS)
    else:
        print(f"Skipping {ANSI_COLOR(username)}")


def _load_stats(stats: List[dict]):
    export = {
        "fide_rapid": None,
    }
    for stat in stats:
        if stat["key"] == "rapid":
            export["fide_rapid"] = stat["stats"]["rating"]
    return export


def _write_export(username: str):
    """Converts downloaded data into JSON format and writes to disk.

    As of now, the following content is exported per-coach:
    * FIDE ratings (number | null)

    Unlike the network-related functions, this method will always overwrite
    files.
    """
    stat_export = {}
    try:
        with open(DATA_COACH_STATS.format(username=username), "r") as f:
            stat_export = _load_stats(json.load(f).get("stats", []))
    except FileNotFoundError:
        print(f"Skipping {username} export")

    export = {}
    export.update(stat_export)
    with open(DATA_COACH_EXPORT.format(username=username), "w") as f:
        json.dump(export, f)


async def _scrape():
    parser = argparse.ArgumentParser(
        prog="chesscom-scraper",
        description="HTML scraping of chess.com coaches.",
    )
    parser.add_argument("-u", "--user-agent", required=True)
    args = parser.parse_args()

    os.makedirs("data/pages", exist_ok=True)
    os.makedirs("data/coach", exist_ok=True)

    async with aiohttp.ClientSession(
        headers={"User-Agent": USER_AGENT.format(user_agent=args.user_agent)}
    ) as session:
        # Retrieve all coaches on the platform.
        usernames = await _scrape_all_coach_usernames(session)
        # For each coach, download relevant data.
        for username in [u.strip() for u in usernames]:
            os.makedirs(DATA_COACH_DIR.format(username=username), exist_ok=True)
            await _download_coach_data(session, username)
            _write_export(username)


def run():
    asyncio.run(_scrape())
