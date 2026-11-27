import email.utils
import html.parser
import logging
import os
import pathlib
import re
import secrets
import tempfile
import unittest
import urllib.parse
import xml.etree.ElementTree

from mkdocs.config import load_config
from mkdocs.structure.files import get_files

logging.disable(logging.CRITICAL)


def project():
    return pathlib.Path(__file__).resolve().parent.parent


class Posts:
    """
    The posts as the author wrote them, the measure the built site is held to.
    """

    def __init__(self, root):
        self.files = sorted(pathlib.Path(root).resolve(strict=True).rglob("*.md"))

    def days(self):
        return sorted((file.name[:10] for file in self.files), reverse=True)


class Head(html.parser.HTMLParser):
    """
    The head of a page as a search engine reads it, kept for its meta description.
    """

    def __init__(self):
        super().__init__()
        self.summary = ""

    def handle_starttag(self, tag, attrs):
        if tag == "meta" and dict(attrs).get("name") == "description":
            self.summary = dict(attrs).get("content") or ""


class Site:
    """
    The site that MkDocs has built, read the way feed readers and crawlers read it.
    """

    def __init__(self, root):
        self.root = pathlib.Path(root)

    def channel(self):
        return xml.etree.ElementTree.parse(self.root / "feed_rss_created.xml").getroot().find("channel")

    def items(self):
        return self.channel().findall("item")

    def file(self, url):
        return self.root / urllib.parse.unquote(urllib.parse.urlparse(url).path).lstrip("/")

    def summary(self, url):
        head = Head()
        head.feed((self.file(url) / "index.html").read_text(encoding="utf-8"))
        return head.summary

    def maps(self):
        lines = (self.root / "robots.txt").read_text(encoding="utf-8").splitlines()
        return [line.partition(":")[2].strip() for line in lines if line.lower().startswith("sitemap:")]


class SiteTest(unittest.TestCase):
    """
    The promises the published site keeps to readers, feed readers and crawlers.
    """

    def test_feed_dates_its_newest_posts_by_their_own_days(self):
        days = sorted(
            (
                email.utils.parsedate_to_datetime(item.findtext("pubDate")).strftime("%Y-%m-%d")
                for item in Site(os.environ["SITE"]).items()
            ),
            reverse=True,
        )
        self.assertEqual(
            Posts(project() / "docs" / "posts").days()[: max(1, len(days))],
            days,
            "feed dates posts by days they were not written on",
        )

    def test_feed_describes_posts_without_html(self):
        tags = re.compile(r"<(h[1-6]|p|a|code|em|strong|ul|ol|li|pre|blockquote|img|br)\b")
        marked = [
            item.findtext("link")
            for item in Site(os.environ["SITE"]).items()
            if tags.search(item.findtext("description", ""))
        ]
        self.assertEqual([], marked, "feed describes posts with HTML")

    def test_feed_shows_an_image_the_site_serves(self):
        site = Site(os.environ["SITE"])
        image = site.channel().findtext("image/url", "")
        self.assertTrue(site.file(image).is_file(), f"feed shows the image {image} that the site doesnt serve")

    def test_pages_repeat_the_description_of_the_feed(self):
        site = Site(os.environ["SITE"])
        strangers = [
            item.findtext("link")
            for item in site.items()
            if site.summary(item.findtext("link")).split() != item.findtext("description", "").split()
        ]
        self.assertEqual([], strangers, "pages describe themselves differently from the feed")

    def test_robots_names_a_sitemap_the_site_serves(self):
        site = Site(os.environ["SITE"])
        maps = site.maps()
        self.assertTrue(
            maps and all(site.file(url).is_file() for url in maps),
            f"robots.txt names the sitemaps {maps} that the site doesnt serve",
        )

    def test_notes_dont_reach_the_site(self):
        with tempfile.TemporaryDirectory() as docs:
            note = pathlib.Path(docs, "superpowers", f"{secrets.token_hex(4)}.md")
            note.parent.mkdir()
            note.write_text("# Notes", encoding="utf-8")
            pathlib.Path(docs, "index.md").write_text("# Home", encoding="utf-8")
            config = load_config(str(project() / "mkdocs.yml"), docs_dir=docs, plugins=[])
            pages = [file.src_uri for file in get_files(config).documentation_pages()]
        self.assertEqual(["index.md"], pages, "notes from docs/superpowers reach the site")
