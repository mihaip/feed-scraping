#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["google-auth-oauthlib>=1.2,<2"]
# ///
"""Create/resume the companion YouTube playlist using the official Data API."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import runpy
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parent
CONFIG = Path.home() / ".config" / "feed-scraping" / "chm-youtube"
TOKEN = CONFIG / "chm-youtube-token.json"
SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
API = "https://www.googleapis.com/youtube/v3/"
TITLE = "CHM Oral Histories — Apple and NeXT"
FEED = (
    "https://github.com/mihaip/feed-scraping/releases/download/"
    "chm-apple/chm-apple.xml"
)


def plan():
    catalog = json.loads((ROOT / "chm-apple-catalog.json").read_text())
    feed = runpy.run_path(str(ROOT / "chm-apple-feed.py"))
    episodes = list(reversed(feed["selected_episodes"](catalog)))
    return {
        "title": TITLE,
        "description": (
            "Computer History Museum oral histories featuring Apple and NeXT employees. "
            "The same episodes as the companion podcast feed, ordered by original "
            "interview recording date, oldest first. Contractors and other ecosystem "
            "connections are excluded. Recordings by the Computer History Museum.\n\n"
            "Companion RSS: " + FEED
        ),
        "privacy": "unlisted",
        "videos": [
            {"video_id": e["video_id"], "title": e["title"],
             "interview_date": e["interview_date"], "url": e["youtube_url"]}
            for e in episodes
        ],
    }


def save_credentials(credentials):
    CONFIG.mkdir(parents=True, exist_ok=True, mode=0o700)
    CONFIG.chmod(0o700)
    with open(TOKEN, "w", opener=lambda path, flags: os.open(path, flags, 0o600)) as file:
        os.fchmod(file.fileno(), 0o600)
        file.write(credentials.to_json())


def authenticate(client_secrets):
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not client_secrets.is_file():
        raise RuntimeError("The OAuth desktop-client JSON file does not exist.")
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), [SCOPE])
    credentials = flow.run_local_server(port=0, prompt="consent")
    save_credentials(credentials)
    print("YouTube authorization saved locally.")


class YouTube:
    def __init__(self):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        if not TOKEN.exists():
            raise RuntimeError("Authorize first: uv run chm-apple/chm-apple-playlist.py auth --client-secrets /path/to/client.json")
        credentials = Credentials.from_authorized_user_file(str(TOKEN), [SCOPE])
        if not credentials.valid:
            credentials.refresh(Request())
            save_credentials(credentials)
        self.token = credentials.token

    def request(self, resource, *, body=None, method=None, **query):
        url = API + resource + "?" + urllib.parse.urlencode(query)
        method = method or ("POST" if body is not None else "GET")
        request = urllib.request.Request(
            url, data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"},
            method=method,
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    return json.load(response)
            except urllib.error.HTTPError as error:
                # A newly created playlist can briefly return 404 when listing items.
                # Only reads are retried; writes are resumed from server state.
                if method == "GET" and error.code in {404, 429, 500, 502, 503, 504} and attempt < 3:
                    error.close()
                    time.sleep(2 ** attempt)
                    continue
                details = json.loads(error.read()).get("error", {})
                raise RuntimeError(f"YouTube API HTTP {error.code}: {details.get('message', 'request failed')}") from None

    def items(self, resource, **query):
        page_token = None
        while True:
            response = self.request(resource, maxResults=50, **query,
                                    **({"pageToken": page_token} if page_token else {}))
            yield from response.get("items", [])
            page_token = response.get("nextPageToken")
            if not page_token:
                break


def save_state(path, state):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def sync(api, expected, state_path):
    expected_ids = [v["video_id"] for v in expected["videos"]]
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    playlist_id = state.get("playlist_id")
    if not playlist_id:
        matches = [p for p in api.items("playlists", part="snippet,status", mine="true")
                   if p["snippet"]["title"] == expected["title"]
                   and "Companion RSS: " + FEED in p["snippet"].get("description", "")]
        if len(matches) > 1:
            raise RuntimeError("Multiple matching playlists exist; select one in the local playlist state before retrying.")
        playlist = matches[0] if matches else api.request(
            "playlists", part="snippet,status", body={
                "snippet": {"title": expected["title"], "description": expected["description"]},
                "status": {"privacyStatus": expected["privacy"]},
            },
        )
        playlist_id = playlist["id"]
        state = {"playlist_id": playlist_id, "url": "https://www.youtube.com/playlist?list=" + playlist_id,
                 "title": expected["title"], "privacy": playlist["status"]["privacyStatus"]}
        save_state(state_path, state)
    existing = [p["snippet"]["resourceId"]["videoId"]
                for p in api.items("playlistItems", part="snippet", playlistId=playlist_id)]
    if set(existing) - set(expected_ids) or len(existing) != len(set(existing)):
        raise RuntimeError("The playlist contains extra or duplicate videos; review it before syncing.")
    if existing != [vid for vid in expected_ids if vid in set(existing)]:
        raise RuntimeError("Existing videos have a different order; review the playlist before syncing.")
    present = set(existing)
    for position, video in enumerate(expected["videos"]):
        vid = video["video_id"]
        if vid in present:
            continue
        # Do not blindly retry mutations: the next run re-reads server state.
        api.request("playlistItems", part="snippet", body={"snippet": {
            "playlistId": playlist_id, "position": position,
            "resourceId": {"kind": "youtube#video", "videoId": vid},
        }})
        present.add(vid)
        print(f"{len(present)}/{len(expected_ids)}: {video['title']}", flush=True)
    actual = [p["snippet"]["resourceId"]["videoId"]
              for p in api.items("playlistItems", part="snippet", playlistId=playlist_id)]
    if actual != expected_ids:
        raise RuntimeError("Playlist verification failed; rerun sync to resume from server state.")
    state.update(verified_at_utc=datetime.now(timezone.utc).isoformat(),
                 order="interview recording date, oldest first", videos=expected["videos"])
    save_state(state_path, state)
    catalog_path = ROOT / "chm-apple-catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog["companion_youtube_playlist_url"] = state["url"]
    save_state(catalog_path, catalog)
    print(f"Verified {len(actual)} videos: {state['url']}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan", help="Print the exact playlist without authentication or writes")
    auth = commands.add_parser("auth", help="Authorize YouTube access using Google's OAuth library")
    auth.add_argument("--client-secrets", type=Path, required=True)
    create = commands.add_parser("sync", help="Create/resume and verify the companion playlist")
    create.add_argument("--state", type=Path, default=ROOT / "chm-apple-playlist.json")
    args = parser.parse_args()
    try:
        if args.command == "plan":
            print(json.dumps(plan(), ensure_ascii=False, indent=2))
        elif args.command == "auth":
            authenticate(args.client_secrets)
        else:
            sync(YouTube(), plan(), args.state)
    except (RuntimeError, urllib.error.URLError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
