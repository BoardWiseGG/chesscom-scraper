import aiohttp
import asyncio
import os
import os.path
import random

from bs4 import BeautifulSoup


# References to paths we use to save any scraped content.
DATA_COACH_LIST = "data/pages/{}.txt"
DATA_COACH_DIR = "data/coach/{}/{}"


async def scrape_coach_links(page_no):
    """Scrape a single coach page listing."""
    links = []
    href = f"https://www.chess.com/coaches?sortBy=alphabetical&page={page_no}"
    async with aiohttp.ClientSession() as session:
        async with session.get(href) as response:
            if response.status != 200:
                print(f"Encountered {response.status} when retrieving {href}.")
                return
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            members = soup.find_all("a", class_="members-categories-blahblah")
            for member in members:
                links.append(member.get("href"))

    return links


async def scrape_all_coach_links(max_pages=64):
    """Scan through https://www.chess.com/coaches for all member links."""
    links = []
    for i in range(1, max_pages + 1):
        filepath = DATA_COACH_LIST.format(i)
        if os.path.isfile(filepath):
            with open(filepath, "r") as f:
                links = f.readlines()
            print(f"{filepath} already exists.")
        else:
            links = await scrape_coach_links(i)
            with open(filepath, "w") as f:
                for link in links:
                    f.write(f"{link}\n")
            print(f"Downloaded page {i} of coach list.")
            await asyncio.sleep(random.randint(3, 7))

    return links


async def download_member_info(member_name, filename, href):
    """Download member-specific content.

    @return: True if we downloaded content. False if the download already
    exists locally.
    """
    target = DATA_COACH_DIR.format(member_name, filename)
    if os.path.isfile(target):
        return False
    async with aiohttp.ClientSession() as session:
        async with session.get(href) as response:
            if response.status != 200:
                print(f"Encountered {response.status} when retrieving {href}")
                return
            with open(target, "w") as f:
                f.write(await response.text())
    return True


async def main():
    links = await scrape_all_coach_links()
    for href in [link.strip() for link in links]:
        member_name = href[len("https://www.chess.com/member/") :]
        downloaded = await asyncio.gather(
            download_member_info(
                member_name,
                f"{member_name}.html",
                href,
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
