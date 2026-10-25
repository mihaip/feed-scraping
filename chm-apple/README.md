# CHM Apple and NeXT oral histories

Generates a podcast RSS feed for Computer History Museum oral histories featuring Apple or NeXT employees. The [catalogue](chm-apple-catalog.json) retains the broader ecosystem research and tentative matches from the full playlist review. The feed requires `status == "include"` and `category in {"apple_employee", "next_employee"}`; contractors and other ecosystem connections are excluded.

From the repository root:

    python3 chm-apple/chm-apple-feed.py > chm-apple/chm-apple.xml

The scraped feed is published as a [GitHub release artifact](https://github.com/mihaip/feed-scraping/releases/download/chm-apple/chm-apple.xml). It combines existing MP3s from the [original podcast feed](https://chm-oral-histories.s3.us-west-1.amazonaws.com/podcast.rss) with supplemental MP3s hosted in the [GitHub release](https://github.com/mihaip/feed-scraping/releases/tag/chm-apple).

Episode dates use the original recording day at noon UTC. Parts recorded on the same day receive successive one-minute offsets so podcast apps sort later parts first in newest-first views. These offsets are ordering hints; the actual recording times are unknown. The artwork uses CHM's official YouTube channel image, since the upstream Oral Histories playlist has an interview-specific thumbnail.

[Companion YouTube playlist](https://www.youtube.com/playlist?list=PLd8A9AOrb7Zo): the same 61 episodes, ordered by recording date, oldest first (unlisted).

The companion YouTube playlist CLI uses the same selection and orders videos by recording date, oldest first. It uses Google's OAuth library through `uv` and requires an OAuth Desktop app client from a project with YouTube Data API v3 enabled:

    uv run chm-apple/chm-apple-playlist.py plan
    uv run chm-apple/chm-apple-playlist.py auth --client-secrets /path/to/client.json
    uv run chm-apple/chm-apple-playlist.py sync

The CLI creates an unlisted playlist and can resume interrupted additions. OAuth credentials stay outside the checkout, in `~/.config/feed-scraping/chm-youtube/`.
