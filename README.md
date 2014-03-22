## gocomics-scrape.py

GoComics.com (which recently merged with Comics.com) changed their RSS feeds to contain at best links only, and at worst links and ads, but no comic.

This script fetches a GoComics.com feed URL and then for each item looks up the the actual comic image (conveniently emebdded in a `<link>` tag) and outputs a minimal Atom feed with the image. Sample usage:

    python gocomics-scrape.py http://feeds.feedburner.com/uclick/frazz \
        ~/www/scraped/frazz.xml

I've put something like that in a cron job that runs once an hour.

Incidentally, Frazz is the comic that I wanted this for, if you're looking for a full content feed for Frazz it can be found at [http://persistent.info/scraped/frazz.xml](http://persistent.info/scraped/frazz.xml).

## dilbert-scrape.py

Dilbert.com also changed its feed so that it now only contains links. This script is a variant of gocomics-scrape.py, but the way the scraping routine locates the image had to be changed significantly. 

## daily-puppy-scrape.py

[The Daily Puppy](http://www.dailypuppy.com/) ostensibly [has an RSS feed](http://feeds.feedburner.com/TheDailyPuppy). However, it has not worked since early January 2014 (the contents are empty). Given that the site also has references to iGoogle ([shut down](https://support.google.com/websearch/answer/2664197?hl=en) on November 1, 2013), it doesn't seem like it's being maintained from a technical perspective. This script scrapes the most recent 10 puppies and generates a (full-content) feed for them (it uses the same XML endpoints as the [the iOS app](https://itunes.apple.com/app/id305199217)).

The result is placed at [http://persistent.info/scraped/daily-puppy.xml](http://persistent.info/scraped/daily-puppy.xml). If the site fixes its offical feed, I will redirect this URL back to the official feed.
