#!/usr/local/bin/python

import datetime
import re
import urllib
import xml.dom.minidom
from xml.sax.saxutils import escape as xml_escape

_BASE_URL = "http://www.dailypuppy.com/mobile/featured-puppy.php"
_XHTML_NS = "http://www.w3.org/1999/xhtml"
_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})$")

class Puppy(object):
  def __init__(self, title, data_url):
    self.title = title
    self.data_url = data_url
    self.date = None
    self.html_url = None
    self.description = None
    self.pictures = []

def open_url(url):
  class Opener(urllib.FancyURLopener):
      version = "Mozilla/5.0 (compatible; Feedbot/1.0)"
  return Opener().open(url)

def _get_node_text(node):
  return node.firstChild.data

def get_puppies():
  puppies_file = open_url(_BASE_URL + "?startIndex=0&count=10")
  puppies_dom = xml.dom.minidom.parse(puppies_file)

  puppies = []
  puppy_nodes = puppies_dom.getElementsByTagName("item")
  for puppy_node in puppy_nodes:
    puppies.append(Puppy(
      title=_get_node_text(puppy_node.getElementsByTagName("title")[0]),
      data_url=_get_node_text(puppy_node.getElementsByTagName("link")[0])))

  puppies_file.close()

  return puppies

def fetch_puppy_data(puppy):
  puppy_file = open_url(puppy.data_url)
  puppy_dom = xml.dom.minidom.parse(puppy_file)

  puppy.html_url = _get_node_text(
    puppy_dom.getElementsByTagName("shareLink")[0])
  date_match = _DATE_RE.search(puppy.html_url)
  puppy.date = datetime.datetime(
    year=int(date_match.group(1)),
    month=int(date_match.group(2)),
    day=int(date_match.group(3)),
    hour=12)
  puppy.description = _get_node_text(
    puppy_dom.getElementsByTagName("description")[0])
  picture_nodes = puppy_dom.getElementsByTagName("fullres")
  for picture_node in picture_nodes:
    puppy.pictures.append(_get_node_text(picture_node))

  puppy_file.close()

puppies = get_puppies()
for puppy in puppies:
  fetch_puppy_data(puppy)

feed = u''
feed += u'<?xml version="1.0" encoding="utf-8"?>\n'
feed += u'<feed xmlns="http://www.w3.org/2005/Atom">\n'
feed += u'<title>The Daily Puppy (Unofficial)</title>\n'
feed += u'<link rel="alternate" type="text/html" ' \
    'href="http://www.dailypuppy.com/"/>\n'

if puppies:
  for puppy in puppies:
    feed += u'<entry>\n'
    feed += u'  <title>%s</title>\n' % xml_escape(puppy.title)
    feed += u'  <id>%s</id>\n' % xml_escape(puppy.data_url)
    feed += u'  <link rel="alternate" href="%s" type="text/html"/>\n' % \
        xml_escape(puppy.html_url)
    feed += u'  <updated>%sZ</updated>\n' % xml_escape(puppy.date.isoformat())
    feed += u'  <content type="xhtml">\n'
    feed += u'    <div xmlns="%s">\n' % _XHTML_NS
    feed += u'    <p><img src="%s"/></p>\n' % xml_escape(puppy.pictures[0])
    feed += u'    <p>%s</p>\n' % xml_escape(puppy.description)
    for picture in puppy.pictures[1:]:
      feed += u'    <p><img src="%s"/></p>\n' % xml_escape(picture)
    feed += u'    </div>\n'
    feed += u'  </content>\n'
    feed += u'</entry>\n'
else:
  feed += u'<entry>\n'
  feed += u'  <title>Could not scrape feed</title>\n'
  feed += u'  <id>tag:persistent.info,2013:daily-puppy-scrape-%d</id>\n' % \
        int(time.time())
  feed += u'  <link rel="alternate" ' \
        'href="https://github.com/mihaip/feed-scraping" type="text/html"/>\n'
  feed += u'  <content type="html">\n'
  feed += u'    Could not scrape the feed. Check the GitHub repository for ' \
        'updates.\n'
  feed += u'  </content>\n'
  feed += u'</entry>\n'

feed += u'</feed>\n'

print feed.encode("utf-8")
