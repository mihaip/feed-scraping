#!/usr/bin/env python3

import datetime
import json
import typing
import subprocess
from xml.sax.saxutils import escape as xml_escape

XHTML_NS = 'http://www.w3.org/1999/xhtml'

class Article(typing.NamedTuple):
    title: str
    url: str
    category: str
    published_date: datetime.datetime

def fetch_articles():
    # We need to shell out to curl because the OpenAI website rejects HTTP 1.1
    # requests.
    result = subprocess.run([
        'curl', 'https://openai.com/backend/pages/?limit=12&sort=new&type=Article',
            '-H', 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            '-H', 'accept-language: en-US,en;q=0.9,ro;q=0.8',
            '-H', 'priority: u=0, i',
            '-H', 'sec-ch-ua: "Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            '-H', 'sec-ch-ua-platform: "macOS"',
            '-H', 'sec-fetch-dest: document',
            '-H', 'sec-fetch-mode: navigate',
            '-H', 'sec-fetch-site: none',
            '-H', 'upgrade-insecure-requests: 1',
            '-H', 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True)

    if result.returncode != 0:
        raise Exception(result.stderr)

    if result.stdout.startswith("<!DOCTYPE html>"):
        raise Exception("OpenAI website rejected the request")

    articles_json = json.loads(result.stdout)
    articles = []
    for article_json in articles_json.get("items", []):
        if article_json.get("pageType") != "Article":
            continue
        published_date_str = article_json["publicationDate"]
        published_date = datetime.datetime.fromisoformat(published_date_str)

        article = Article(
            title=article_json["title"],
            url=f"https://openai.com{article_json['slug']}",
            published_date=published_date,
            category=article_json.get("category", {}).get("name"),
        )
        articles.append(article)

    return sorted(articles, key=lambda t: t.published_date, reverse=True)


print('<?xml version="1.0" encoding="utf-8"?>')
print('<feed xmlns="http://www.w3.org/2005/Atom">')
print('<title>OpenAI News (Unofficial)</title>')
print('<link rel="alternate" type="text/html" href="https://openai.com/news/"/>')

strip_count = 0
for article in fetch_articles():
  print('<entry>')
  print('  <title>%s</title>' % article.title)
  print('  <id>%s</id>' % xml_escape(article.url))
  print('  <published>%sT12:00:00.000Z</published>' % article.published_date.isoformat())
  print('  <link rel="alternate" href="%s" type="text/html"/>' % xml_escape(article.url))
  if article.category:
    print('  <category term="%s"/>' % xml_escape(article.category))
  print('</entry>')

print('</feed>')
