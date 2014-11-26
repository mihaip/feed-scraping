#!/usr/local/bin/python

import formatter
import htmllib
import sys
import time
import urllib
import xml.dom.minidom
from xml.sax.saxutils import escape as xml_escape

def open_url(url):
  class Opener(urllib.FancyURLopener):
    version = 'Mozilla/5.0 (compatible; Feedbot/1.0)'

  return Opener().open(url)

class Post(object):
  def __init__(self, url):
    self.url = url
    self.title = ""

class PostsPageParser(htmllib.HTMLParser):
  def __init__(self):
    htmllib.HTMLParser.__init__(self, formatter.NullFormatter())
    self.posts = []
    self._current_post = None

  def start_a(self, attrs):
    attrs = dict(attrs)
    href = attrs.get("href", "")
    if href.startswith("/posts/") and len(href) > 24:
      self._current_post = Post("https://code.facebook.com" + href)
      self.posts.append(self._current_post)

  def end_a(self):
    if self._current_post:
      self._current_post = None

  def handle_data(self, data):
    if self._current_post:
      self._current_post.title += data

def get_posts():
  posts_parser = PostsPageParser()
  posts_file = open_url("https://code.facebook.com/posts/")
  posts_parser.feed(posts_file.read())
  posts_parser.close()
  posts_file.close()

  return posts_parser.posts

posts = get_posts()

print '<?xml version="1.0" encoding="utf-8"?>'
print '<feed xmlns="http://www.w3.org/2005/Atom">'
print '<title>Facebook Engineering Blog</title>'
print '<link rel="alternate" href="https://code.facebook.com/posts/" type="text/html"/>'

for post in posts:
  print '<entry>'
  print '  <title>%s</title>' % xml_escape(post.title)
  print '  <id>%s</id>' % xml_escape(post.url)
  print '  <link rel="alternate" href="%s" type="text/html"/>' % xml_escape(post.url)
  print '</entry>'

if not posts:
  print '<entry>'
  print '  <title>Could not scrape feed</title>'
  print '  <id>tag:persistent.info,2014:facebook-code-scrape-%d</id>' % int(time.time())
  print '  <link rel="alternate" href="https://github.com/mihaip/feed-scraping" type="text/html"/>'
  print '  <content type="html">'
  print '    Could not scrape the feed. Check the GitHub repository for updates.'
  print '  </content>'
  print '</entry>'


print '</feed>'
