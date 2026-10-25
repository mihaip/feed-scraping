#!/usr/bin/env python3
"""Generate a podcast RSS feed of CHM oral histories featuring Apple/NeXT employees."""

import argparse
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
FEED_URL = (
    "https://github.com/mihaip/feed-scraping/releases/download/"
    "chm-apple/chm-apple.xml"
)
ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"
ET.register_namespace("itunes", ITUNES)
ET.register_namespace("atom", ATOM)


def recording_date(episode):
    # Sources give a day, not a time. Noon UTC also keeps that day in US time zones.
    # Fail on missing dates rather than quietly mixing in YouTube upload dates.
    recorded = datetime.strptime(episode["interview_date"], "%Y-%m-%d")
    return recorded.replace(hour=12, tzinfo=timezone.utc)


def recording_order(episode):
    # Later parts come first in the descending feed when recorded on the same day.
    parts = tuple(int(n) for n in re.findall(r"\b(?:part|session)\s+(\d+)", episode["title"], re.I))
    return recording_date(episode), parts, episode["video_id"]


def selected_episodes(catalog):
    episodes = [
        e for e in catalog["episodes"]
        if e["status"] == "include" and e["category"] in {"apple_employee", "next_employee"}
    ]
    episodes.sort(key=recording_order, reverse=True)
    if not episodes or len({e["video_id"] for e in episodes}) != len(episodes):
        raise ValueError("Expected a nonempty catalogue with unique video IDs")
    return episodes


def rss_dates(episodes):
    # Clients may ignore XML order when pubDate ties. Offset successive parts by
    # one minute within the recording day; these are ordering hints, not real times.
    dates = {}
    offsets = {}
    for episode in sorted(episodes, key=recording_order):
        day = episode["interview_date"]
        offset = offsets.get(day, 0)
        dates[episode["video_id"]] = recording_date(episode) + timedelta(minutes=offset)
        offsets[day] = offset + 1
    return dates


def generate_feed(catalog, audio, feed_url=FEED_URL):
    episodes = selected_episodes(catalog)
    dates = rss_dates(episodes)

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Computer History Museum: Apple Oral Histories (Unofficial)"
    ET.SubElement(channel, "link").text = catalog.get("companion_youtube_playlist_url", catalog["playlist_url"])
    if artwork := catalog.get("artwork"):
        ET.SubElement(channel, f"{{{ITUNES}}}image", href=artwork["url"])
        image = ET.SubElement(channel, "image")
        ET.SubElement(image, "url").text = artwork["url"]
        ET.SubElement(image, "title").text = channel.findtext("title")
        ET.SubElement(image, "link").text = channel.findtext("link")
        ET.SubElement(image, "width").text = "144"
        ET.SubElement(image, "height").text = "144"
    ET.SubElement(channel, "description").text = (
        "A curated selection of Computer History Museum oral histories featuring "
        "people who worked as Apple or NeXT employees. "
        "Episodes use their original interview recording dates. "
        "An unofficial feed; recordings are by the Computer History Museum."
    )
    ET.SubElement(channel, "language").text = "en"
    ET.SubElement(channel, "copyright").text = "Recordings © Computer History Museum"
    ET.SubElement(channel, "pubDate").text = format_datetime(dates[episodes[0]["video_id"]], usegmt=True)
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(datetime.now(timezone.utc), usegmt=True)
    ET.SubElement(channel, f"{{{ATOM}}}link", href=feed_url, rel="self", type="application/rss+xml")
    ET.SubElement(channel, f"{{{ITUNES}}}author").text = "Computer History Museum"
    ET.SubElement(channel, f"{{{ITUNES}}}explicit").text = "false"
    ET.SubElement(channel, f"{{{ITUNES}}}type").text = "episodic"
    ET.SubElement(channel, f"{{{ITUNES}}}category", text="Technology")

    for episode in episodes:
        video_id = episode["video_id"]
        media = audio["episodes"][video_id]
        if urlparse(media["url"]).scheme != "https" or not isinstance(media["length"], int) or media["length"] <= 0:
            raise ValueError(f"Invalid enclosure: {video_id}")
        if media["type"] != "audio/mpeg":
            raise ValueError(f"Expected MP3 audio: {video_id}")

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = episode["title"]
        ET.SubElement(item, "link").text = episode["youtube_url"]
        ET.SubElement(item, "guid", isPermaLink="true").text = episode["youtube_url"]
        ET.SubElement(item, "pubDate").text = format_datetime(dates[video_id], usegmt=True)
        description = [episode["connection"]]
        if episode.get("interview_date"):
            description.append(f"Interview recorded: {episode['interview_date']}.")
        description.append(f"Originally published on YouTube: {episode['youtube_publish_date']}.")
        description.append(f"Original video: {episode['youtube_url']}")
        for source in episode.get("sources", []):
            if source["kind"] == "chm_catalog":
                description.append(f"CHM catalogue: {source['url']}")
        ET.SubElement(item, "description").text = "\n\n".join(description)
        ET.SubElement(item, "enclosure", url=media["url"], length=str(media["length"]), type=media["type"])
        ET.SubElement(item, f"{{{ITUNES}}}duration").text = str(round(episode["duration_seconds"]))
        ET.SubElement(item, f"{{{ITUNES}}}explicit").text = "false"

    ET.indent(rss, space="  ")
    return ET.tostring(rss, encoding="utf-8", xml_declaration=True) + b"\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "chm-apple-catalog.json")
    parser.add_argument("--audio", type=Path, default=ROOT / "chm-apple-audio.json")
    parser.add_argument("--feed-url", default=FEED_URL)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text())
    audio = json.loads(args.audio.read_text())
    sys.stdout.buffer.write(generate_feed(catalog, audio, args.feed_url))
