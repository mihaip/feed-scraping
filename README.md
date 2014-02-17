## gocomics-scrape.py

GoComics.com (which recently merged with Comics.com) changed their RSS feeds to contain at best links only, and at worst links and ads, but no comic.

This script fetches a GoComics.com feed URL and then for each item looks up the the actual comic image (conveniently emebdded in a `<link>` tag) and outputs a minimal Atom feed with the image. Sample usage:

    python gocomics-scrape.py http://feeds.feedburner.com/uclick/frazz \
        ~/www/scraped/frazz.xml

I've put something like that in a cron job that runs once an hour.

Incidentally, Frazz is the comic that I wanted this for, if you're looking for a full content feed for Frazz it can be found at [http://persistent.info/scraped/frazz.xml](http://persistent.info/scraped/frazz.xml).
