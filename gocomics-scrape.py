#!/usr/local/bin/python

import datetime
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
    headers={'User-Agent': 'Mozilla/5.0 (compatible; Feedbot/1.0)'})

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
  parser.feed(homepage_file.read().decode())
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
      self.in_comic_viewer = False
      self.tag_attrs_stack = []

    def handle_starttag(self, tag, attrs):
      self.tag_attrs_stack.append(attrs)
      if self.is_comic_viewer(tag, attrs):
        if self.in_comic_viewer:
          logging.warning("Nested comic viewer divs found")
        self.in_comic_viewer = True

    def handle_endtag(self, tag):
      attrs = self.tag_attrs_stack.pop()
      if self.is_comic_viewer(tag, attrs):
        self.in_comic_viewer = False

    def handle_startendtag(self, tag, attrs):
      if self.in_comic_viewer and self.is_comic_image(tag, attrs):
        if self.image_url:
          logging.warning("Multiple comic image tags found")
        self.image_url = dict(attrs).get('src', None)

    def is_comic_viewer(self, tag, attrs):
      class_name = dict(attrs).get('class', '')
      return tag == 'div' and 'ComicViewer_comicViewer__comic' in class_name

    def is_comic_image(self, tag, attrs):
      class_name = dict(attrs).get('class', '')
      return tag == 'img' and 'Comic_comic__image' in class_name

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
  parser.feed(strip_file.read().decode())
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
  print('  <id>tag:persistent.info,2013:gocomics-scrape-%d</id>' % int(time.time()))
  print('  <link rel="alternate" href="https://github.com/mihaip/feed-scraping" type="text/html"/>')
  print('  <content type="html">')
  print('    Could not scrape the feed. Check the GitHub repository for updates.')
  print('  </content>')
  print('</entry>')


print('</feed>')
