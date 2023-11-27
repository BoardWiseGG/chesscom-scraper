import aiohttp
import asyncio
import os
import os.path
import random

from bs4 import BeautifulSoup


# References to paths we use to save any scraped content.
DATA_COACH_LINKS = "data/coach_links.txt"
DATA_COACH_DIR = "data/coach/{}/{}"


async def scrape_coach_links(page_no):
    """Scrape a single coach page listing."""
    links = []
    async with aiohttp.ClientSession() as session:
        href = f"https://www.chess.com/coaches?sortBy=alphabetical&page={page_no}"
        async with session.get(href) as response:
            if response.status != 200:
                print(f"Encountered {response.status} when retrieving {href}")
                return
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            members = soup.find_all("a", class_="members-categories-username")
            for member in members:
                links.append(member.get("href"))

    return links


async def scrape_all_coach_links(max_pages=62):
    """Scans through chess.com/coaches for all member links."""
    if os.path.isfile(DATA_COACH_LINKS):
        with open(DATA_COACH_LINKS, "r") as f:
            return f.readlines()
    for i in range(1, max_pages + 1):
        # Nest the file context manager here so I can `tail -f` the file.
        with open(DATA_COACH_LINKS, "a") as f:
            links = await scrape_coach_links(i)
            for link in links:
                f.write(f"{link}\n")
            await asyncio.sleep(random.randint(2, 5))
    return links


async def download_member_info(member_name, filename, href):
    """Download member-specific content.

    @return: True if we downloaded content. False if the results already
    existed locally.
    """
    target = DATA_COACH_DIR.format(member_name, filename)
    if os.path.isfile(target):
        return False
    with open(target, "w") as f:
        async with aiohttp.ClientSession() as session:
            async with session.get(href) as response:
                if response.status != 200:
                    print(f"Encountered {response.status} when retrieving {href}")
                    return
                f.write(await response.text())
    return True


async def main():
    links = await scrape_all_coach_links()
    for link in links:
        href = link.strip()
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
        # Only want to sleep if the files didn't already exist.
        if any(downloaded):
            await asyncio.sleep(random.randint(2, 5))
            print(f"Downloaded {member_name}")
        else:
            print(f"Skipping {member_name}")


if __name__ == "__main__":
    os.makedirs("data/coach", exist_ok=True)
    asyncio.run(main())
