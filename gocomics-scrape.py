#!/usr/local/bin/python

import datetime
import http.client
import logging
import html.parser
import re
import sys
import time
import urllib.request
from xml.sax.saxutils import escape as xml_escape

XHTML_NS = 'http://www.w3.org/1999/xhtml'

def open_url(url):
  req = urllib.request.Request(
    url,
    headers={
      'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
      'accept-language': 'en-US,en;q=0.9',
      'priority': 'u=0, i',
      'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': '"macOS"',
      'sec-fetch-dest': 'document',
      'sec-fetch-mode': 'navigate',
      'sec-fetch-site': 'none',
      'sec-fetch-user': '?1',
      'upgrade-insecure-requests': '1',
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36' ,
    })

  return urllib.request.urlopen(req)


def get_homepage_data(strip_id):
  class HomepageParser(html.parser.HTMLParser):
    def __init__(self):
      super().__init__()
      self.title = ''
      self.in_title = False

    def handle_starttag(self, tag, attrs):
      if tag == 'title' and not self.title:
        self.in_title = True

    def handle_endtag(self, tag):
      if tag == 'title':
        self.in_title = False

    def handle_data(self, data):
      if self.in_title:
        self.title += data
        self.title = re.sub(r"\s*\|.*$", "", self.title)

  homepage_url = 'https://www.gocomics.com/%s' % strip_id
  homepage_file = open_url(homepage_url)
  parser = HomepageParser()
  try:
    parser.feed(homepage_file.read().decode())
  except http.client.IncompleteRead as e:
    logging.warning("Incomplete read for homepage %s: %s", homepage_url, e)
    parser.feed(e.partial.decode())
  parser.close()
  homepage_file.close()

  if not parser.title:
    return None, []

  today = datetime.date.today()
  strips = []
  for i in range(0, 14):
    strip_date = today - datetime.timedelta(days=i)
    strip_url = '%s/%s' % (homepage_url, strip_date.strftime('%Y/%m/%d'))
    strips.append((strip_date, strip_url))

  return parser.title, strips


def get_strip_image_url(strip_url):
  class ImageParser(html.parser.HTMLParser):
    def __init__(self):
      super().__init__()
      self.image_url = None

    def handle_startendtag(self, tag, attrs):
      if tag == "meta":
        attrs_dict = dict(attrs)
        if attrs_dict.get('property') == 'og:image' and attrs_dict.get('content'):
          if self.image_url:
            logging.warning("Multiple image tags found")
          self.image_url = attrs_dict["content"]

  parser = ImageParser()
  try:
    strip_file = open_url(strip_url)
  except IOError as e:
    if 302 in e.args:
        # Skip over strip URLs that generate redirects, they must not have
        # existed.
        return None
    else:
        logging.warning("Could not extract strip URL", exc_info=True)
        return None
  try:
    parser.feed(strip_file.read().decode())
  except http.client.IncompleteRead as e:
    logging.warning("Incomplete read for strip %s: %s", strip_url, e)
    parser.feed(e.partial.decode())
  parser.close()
  strip_file.close()

  return parser.image_url


title, strips = get_homepage_data(sys.argv[1])

print('<?xml version="1.0" encoding="utf-8"?>')
print('<feed xmlns="http://www.w3.org/2005/Atom">')
print('<title>%s</title>' % xml_escape(title))

strip_count = 0
for strip_date, strip_url in strips:
  strip_image_url = get_strip_image_url(strip_url)
  if not strip_image_url:
    continue
  strip_count += 1
  print('<entry>')
  print('  <title>%s</title>' % xml_escape(strip_date.strftime('%A, %B %d, %Y')))
  print('  <id>%s</id>' % xml_escape(strip_url))
  print('  <published>%sT12:00:00.000Z</published>' % strip_date.isoformat())
  print('  <link rel="alternate" href="%s" type="text/html"/>' % xml_escape(strip_url))
  print('  <content type="xhtml">')
  print('    <div xmlns="%s"><img src="%s"/></div>' % (XHTML_NS, xml_escape(strip_image_url)))
  print('  </content>')
  print('</entry>')

if not strip_count:
  print('<entry>')
  print('  <title>Could not scrape feed</title>')
  print('  <id>tag:persistent.info,2013:gocomics-scrape-error-%s</id>' % datetime.date.today().isoformat())
  print('  <link rel="alternate" href="https://github.com/mihaip/feed-scraping" type="text/html"/>')
  print('  <content type="html">')
  print('    Could not scrape the feed. Check the GitHub repository for updates.')
  print('  </content>')
  print('</entry>')


print('</feed>')
