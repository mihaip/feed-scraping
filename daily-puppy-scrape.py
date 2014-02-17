#!/usr/local/bin/python

import datetime
import re
import urllib
import xml.dom.minidom
from xml.sax.saxutils import escape as xml_escape

_BASE_URL = "http://www.dailypuppy.com/mobile/featured-puppy.php"
_XHTML_NS = 'http://www.w3.org/1999/xhtml'
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
      version = 'Mozilla/5.0 (compatible; Feedbot/1.0)'
  return Opener().open(url)

def _get_node_text(node):
  return node.firstChild.data

def get_puppies():
  puppies_file = open_url(_BASE_URL + "?startIndex=0&count=10")
  puppies_dom = xml.dom.minidom.parse(puppies_file)

  puppies = []
  puppy_nodes = puppies_dom.getElementsByTagName('item')
  for puppy_node in puppy_nodes:
    puppies.append(Puppy(
      title=_get_node_text(puppy_node.getElementsByTagName('title')[0]),
      data_url=_get_node_text(puppy_node.getElementsByTagName('link')[0])))

  puppies_file.close()

  return puppies

def fetch_puppy_data(puppy):
  puppy_file = open_url(puppy.data_url)
  puppy_dom = xml.dom.minidom.parse(puppy_file)

  puppy.html_url = _get_node_text(
    puppy_dom.getElementsByTagName('shareLink')[0])
  date_match = _DATE_RE.search(puppy.html_url)
  puppy.date = datetime.datetime(
    year=int(date_match.group(1)),
    month=int(date_match.group(2)),
    day=int(date_match.group(3)),
    hour=12)
  puppy.description = _get_node_text(
    puppy_dom.getElementsByTagName('description')[0])
  picture_nodes = puppy_dom.getElementsByTagName('fullres')
  for picture_node in picture_nodes:
    puppy.pictures.append(_get_node_text(picture_node))

  puppy_file.close()

puppies = get_puppies()
for puppy in puppies:
  fetch_puppy_data(puppy)

print '<?xml version="1.0" encoding="utf-8"?>'
print '<feed xmlns="http://www.w3.org/2005/Atom">'
print '<title>The Daily Puppy (Unofficial)</title>'

if puppies:
  for puppy in puppies:
    print '<entry>'
    print '  <title>%s</title>' % xml_escape(puppy.title)
    print '  <id>%s</id>' % xml_escape(puppy.data_url)
    print '  <link rel="alternate" href="%s" type="text/html"/>' % xml_escape(puppy.html_url)
    print '  <updated>%sZ</updated>' % xml_escape(puppy.date.isoformat())
    print '  <content type="xhtml">'
    print '    <div xmlns="%s">' % _XHTML_NS
    print '    <p><img src="%s"/></p>' % xml_escape(puppy.pictures[0])
    print '    <p>%s</p>' % xml_escape(puppy.description)
    for picture in puppy.pictures[1:]:
      print '    <p><img src="%s"/></p>' % xml_escape(picture)
    print '    </div>'
    print '  </content>'
    print '</entry>'
else:
  print '<entry>'
  print '  <title>Could not scrape feed</title>'
  print '  <id>tag:persistent.info,2013:daily-puppy-scrape-%d</id>' % int(time.time())
  print '  <link rel="alternate" href="https://github.com/mihaip/feed-scraping" type="text/html"/>'
  print '  <content type="html">'
  print '    Could not scrape the feed. Check the GitHub repository for updates.'
  print '  </content>'
  print '</entry>'

print '</feed>'
