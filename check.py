from __future__ import annotations
import pushover
import requests
from os import path
from bs4 import BeautifulSoup, Tag
import re
import dataclasses
import textwrap
from csv import DictWriter, DictReader
from typing import List
import logging
import sys

logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

CURRENT_DIRECTORY = path.dirname(__file__)

PAGE_URL = "https://www.independent.co.uk/extras/indybest/gadgets-tech/video-games-consoles/ps5-console-uk-restock-news-latest-b2012447.html"  # noqa: E501

POST_ID_PATTERN = re.compile(r"^post-\d+$")

POST_STORAGE_FILE = path.join(CURRENT_DIRECTORY, "post-storage.csv")


def _is_post(tag: Tag) -> bool:
    """Determine whether the tag is a "post" on the live blog."""
    if tag.name == "div":
        return bool(POST_ID_PATTERN.match(tag.attrs.get("id", "")))
    else:
        return False


@dataclasses.dataclass
class Post:
    id: str
    title: str

    @classmethod
    def from_tag(cls, tag: Tag) -> Post:
        contents = [ss for ss in tag.stripped_strings]
        # First string appears to be a timestamp
        title_full = " ".join(contents[1:])
        title = textwrap.shorten(title_full, width=100, placeholder="...")
        id = tag.attrs["id"]

        return cls(id, title)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class PostStorage:
    def __init__(self, file=POST_STORAGE_FILE, fieldnames=Post.__dataclass_fields__.keys()):
        self._fieldnames = fieldnames

        if path.isfile(file):
            with open(file) as read_file:
                reader = DictReader(read_file)
                self._existing_posts = [Post(**row) for row in reader]
        else:
            logging.info("No existing file")
            self._existing_posts = []

    def new_posts(self, posts: List[Post]) -> List[Post]:
        existing_ids = [ex.id for ex in self._existing_posts]

        return list(filter(lambda p: p.id not in existing_ids, posts))

    def store_posts(self, posts: List[Post]):
        with open(POST_STORAGE_FILE, "w") as write_file:
            writer = DictWriter(write_file, fieldnames=self._fieldnames)
            writer.writeheader()
            for p in [*posts, *self._existing_posts]:
                writer.writerow(p.to_dict())


if __name__ == "__main__":
    page_resp = requests.get(PAGE_URL)
    page_resp.raise_for_status()

    soup = BeautifulSoup(page_resp.text, features="html.parser")
    post_tags = soup.find_all(_is_post)

    posts = [Post.from_tag(tag) for tag in post_tags]

    storage = PostStorage()
    new_posts = storage.new_posts(posts)

    if new_posts:
        logging.info(f"{len(new_posts)} posts to notify")
        pushover_cli = pushover.PushoverClient(configfile=path.join(CURRENT_DIRECTORY, "pushover.conf"))

        notified: List[Post] = []

        for np in new_posts:
            logging.info(f"Sending post to pushover: {np}")
            message_title = f"({np.id.removeprefix('post-')}) - {np.title}"
            pushover_cli.send_message(message_title, url=PAGE_URL, url_title="Live Blog here")
            notified.append(np)

        storage.store_posts(notified)
        logging.info("Stored newly-notified posts")
    else:
        logging.info("No new posts to notify about")
