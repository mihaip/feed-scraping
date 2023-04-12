#!/usr/bin/env python3

import datetime
import json
import os
import typing
import urllib.request
from xml.sax.saxutils import escape as xml_escape

XHTML_NS = 'http://www.w3.org/1999/xhtml'

DATES_PATH = os.path.join(os.path.dirname(__file__), 'apple-technotes-dates.json')

class Technote(typing.NamedTuple):
    title: str
    url: str
    summary: str
    published_date: datetime.datetime

def open_url(url):
  req = urllib.request.Request(
    url,
    headers={'User-Agent': 'Mozilla/5.0 (compatible; Feedbot/1.0)'})

  return urllib.request.urlopen(req)

def get_segment_text(s):
    return s.get("text") or s.get("code") or ""

def fetch_technotes():
    with open_url("https://developer.apple.com/tutorials/data/documentation/Technotes.json") as f:
        technotes_json = json.load(f)

    try:
        with open(DATES_PATH) as f:
            dates_json = json.load(f)
    except FileNotFoundError:
        dates_json = {}

    technotes = []
    for reference_json in technotes_json.get("references", {}).values():
        if reference_json.get("role") != "article":
            continue
        technote_json = reference_json
        published_date_str = dates_json.get(technote_json["identifier"])
        if published_date_str:
            published_date = datetime.datetime.fromisoformat(published_date_str)
        else:
            published_date = datetime.datetime.now()
            dates_json[technote_json["identifier"]] = published_date.isoformat()
        technote = Technote(
            title=technote_json["title"],
            url=f"https://developer.apple.com{technote_json['url']}",
            summary="".join([get_segment_text(a) for a in technote_json["abstract"]]),
            published_date=published_date,
        )
        technotes.append(technote)

    with open(DATES_PATH, "w") as f:
        json.dump(dates_json, f, indent=2)
    return sorted(technotes, key=lambda t: t.published_date, reverse=True)


print('<?xml version="1.0" encoding="utf-8"?>')
print('<feed xmlns="http://www.w3.org/2005/Atom">')
print('<title>Apple Technotes (Unofficial)</title>')
print('<link rel="alternate" type="text/html" href="https://developer.apple.com/documentation/technotes"/>')

strip_count = 0
for technote in fetch_technotes():
  print('<entry>')
  print('  <title>%s</title>' % technote.title)
  print('  <id>%s</id>' % xml_escape(technote.url))
  print('  <published>%sT12:00:00.000Z</published>' % technote.published_date.isoformat())
  print('  <link rel="alternate" href="%s" type="text/html"/>' % xml_escape(technote.url))
  print('  <content type="xhtml">')
  print('    <div xmlns="%s">%s</div>' % (XHTML_NS, xml_escape(technote.summary)))
  print('  </content>')
  print('</entry>')

print('</feed>')
