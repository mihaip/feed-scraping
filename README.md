## apple-technotes-scrape.py

In early 2022 Apple launched [a new technotes site](https://developer.apple.com/documentation/Technotes). It's updated regularly, but does not have a feed. This script scrapes the JSON metadata for the catalog and generates a feed for it. Publication dates for the technotes are inferred based on the first time that a given note is seen.

The scraped feed is published at [https://persistent.info/scraped/apple-technotes.xml](https://persistent.info/scraped/apple-technotes.xml).

## gocomics-scrape.py

GoComics.com (which recently merged with Comics.com) has stopped linking to or updating their RSS feeds.

This script fetches a GoComics.com strip homepage, generates strip URLs and then for each one looks up the the actual comic image and outputs a minimal Atom feed with the image. Sample usage:

    python gocomics-scrape.py frazz > ~/www/scraped/frazz.xml

I've put something like that in a cron job that runs once an hour.

Incidentally, Frazz and Calvin and Hobbes are the comics that I wanted this for, so if you're looking for a full content feeds for them they can be found at [https://persistent.info/scraped/frazz.xml](https://persistent.info/scraped/frazz.xml) and [https://persistent.info/scraped/calvinandhobbes.xml](https://persistent.info/scraped/calvinandhobbes.xml).

## daily-puppy-scrape.py

[The Daily Puppy](http://www.dailypuppy.com/) ostensibly [has an RSS feed](http://feeds.feedburner.com/TheDailyPuppy). However, it has not worked since early January 2014 (the contents are empty). Given that the site also has references to iGoogle ([shut down](https://support.google.com/websearch/answer/2664197?hl=en) on November 1, 2013), it doesn't seem like it's being maintained from a technical perspective. This script scrapes the most recent 10 puppies and generates a (full-content) feed for them (it uses the same XML endpoints as the [the iOS app](https://itunes.apple.com/app/id305199217)).

The result is placed at [http://persistent.info/scraped/daily-puppy.xml](http://persistent.info/scraped/daily-puppy.xml). If the site fixes its offical feed, I will redirect this URL back to the official feed.
