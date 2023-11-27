import aiohttp
import asyncio
import os
import os.path
import random

from bs4 import BeautifulSoup


# References to paths we use to save any scraped content.
DATA_COACH_LIST = "data/pages/{page_no}.txt"
DATA_COACH_DIR = "data/coach/{member_name}"
DATA_COACH_FILE = "data/coach/{member_name}/{filename}"


async def chesscom_requeset(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Encountered {response.status} when retrieving {url}.")
                return response.text()
    pass


async def scrape_coach_links(page_no):
    """Scrape a single coach page listing."""
    links = []
    url = f"https://www.chess.com/coaches?sortBy=alphabetical&page={page_no}"
    async with aiohttp.ClientSession(
        headers={
            "User-Agent": "BoardWise (https://github.com/BoardWiseGG/chesscom-scraper)",
        }
    ) as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Encountered {response.status} when retrieving {url}.")
                return
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            members = soup.find_all("a", class_="members-categories-username")
            for member in members:
                links.append(member.get("href"))

    return links


async def scrape_all_coach_links(max_pages=64):
    """Scan through https://www.chess.com/coaches for all member links."""
    links = []
    for i in range(1, max_pages + 1):
        filepath = DATA_COACH_LIST.format(page_no=i)
        if os.path.isfile(filepath):
            with open(filepath, "r") as f:
                links.extend(f.readlines())
            print(f"{filepath} already exists.")
        else:
            links.extend(await scrape_coach_links(i))
            with open(filepath, "w") as f:
                for link in links:
                    f.write(f"{link}\n")
            print(f"Downloaded page {i} of coach list.")
            await asyncio.sleep(random.randint(3, 7))

    return links


async def download_member_info(member_name, filename, url):
    """Download member-specific content.

    @return: True if we downloaded content. False if the download already
    exists locally.
    """
    filepath = DATA_COACH_FILE.format(member_name=member_name, filename=filename)
    if os.path.isfile(filepath):
        return False
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Encountered {response.status} when retrieving {url}")
                return
            with open(filepath, "w") as f:
                f.write(await response.text())
    return True


async def main():
    links = await scrape_all_coach_links()
    for url in [link.strip() for link in links]:
        member_name = url[len("https://www.chess.com/member/") :]
        os.makedirs(DATA_COACH_DIR.format(member_name=member_name), exist_ok=True)
        downloaded = await asyncio.gather(
            download_member_info(
                member_name,
                f"{member_name}.html",
                url,
            ),
            download_member_info(
                member_name,
                "activity.json",
                f"https://www.chess.com/callback/member/activity/{member_name}?page=1",
            ),
            download_member_info(
                member_name,
                "stats.json",
                f"https://www.chess.com/callback/member/stats/{member_name}",
            ),
        )
        if any(downloaded):
            await asyncio.sleep(random.randint(3, 7))
            print(f"Downloaded {member_name} info.")
        else:
            print(f"Skipping {member_name} download.")


if __name__ == "__main__":
    os.makedirs("data/pages", exist_ok=True)
    os.makedirs("data/coach", exist_ok=True)
    asyncio.run(main())
