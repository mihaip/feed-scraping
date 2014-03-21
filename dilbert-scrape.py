#!/usr/local/bin/python

import formatter
import htmllib
import sys
import time
import urllib
import xml.dom.minidom
from xml.sax.saxutils import escape as xml_escape

FEEDBURNER_NS = 'http://rssnamespace.org/feedburner/ext/1.0'
XHTML_NS = 'http://www.w3.org/1999/xhtml'

def open_url(url):
  class Opener(urllib.FancyURLopener):
      version = 'Mozilla/5.0 (compatible; Feedbot/1.0)'

  return Opener().open(url)

def get_feed_data(feed_url):
  items = []

  feed_file = open_url(feed_url)
  feed_dom = xml.dom.minidom.parse(feed_file)

  feed_title = feed_dom.getElementsByTagName('title')[0].firstChild.data
  feed_title = feed_title.replace('GoComics.com - ', '')

  item_nodes = feed_dom.getElementsByTagName('item')
  for item_node in item_nodes:
    item_title = item_node.getElementsByTagName('title')[0].firstChild.data
    # item_link = item_node.getElementsByTagNameNS(FEEDBURNER_NS, 'origLink')[0].firstChild.data
    item_link = item_node.getElementsByTagName('guid')[0].firstChild.data
    items.append((item_title, item_link))
  feed_file.close()

  return feed_title, items

def get_item_image_url(item_url):
  class ImageLinkParser(htmllib.HTMLParser):
      def __init__(self):
          htmllib.HTMLParser.__init__(self, formatter.NullFormatter())
          self.image_url = None

      def do_img(self, attrs):
        if ('title', 'The Dilbert Strip for') in attrs:
          self.image_url = dict(attrs).get('src', None)

  parser = ImageLinkParser()
  item_file = open_url(item_url)
  parser.feed(item_file.read())
  parser.close()
  item_file.close()

  return parser.image_url

title, items = get_feed_data(sys.argv[1])

print '<?xml version="1.0" encoding="utf-8"?>'
print '<feed xmlns="http://www.w3.org/2005/Atom">'
print '<title>%s</title>' % xml_escape(title)

item_count = 0
for item_title, item_url in items:
  item_image_url = get_item_image_url(item_url)
  if not item_image_url:
    continue
  item_count += 1
  print '<entry>'
  print '  <title>%s</title>' % xml_escape(item_title)
  print '  <id>%s</id>' % item_url
  print '  <link rel="alternate" href="%s" type="text/html"/>' % xml_escape(item_url)
  print '  <content type="xhtml">'
  print '    <div xmlns="%s"><img src="%s"/></div>' % (XHTML_NS, xml_escape(item_image_url))
  print '  </content>'
  print '</entry>'

if not item_count:
  print '<entry>'
  print '  <title>Could not scrape feed</title>'
  print '  <id>tag:persistent.info,2013:gocomics-scrape-%d</id>' % int(time.time())
  print '  <link rel="alternate" href="https://github.com/mihaip/feed-scraping" type="text/html"/>'
  print '  <content type="html">'
  print '    Could not scrape the feed. Check the GitHub repository for updates.'
  print '  </content>'
  print '</entry>'


print '</feed>'
