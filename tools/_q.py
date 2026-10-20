# -*- coding: utf-8 -*-
import requests, feedparser
queries = ["\u041e\u0434\u0435\u0441\u0441\u0430 \u0422\u0426\u041a \u0446\u044b\u0433\u0430\u043d\u0435 \u043a\u0430\u043c\u043d\u0438", "\u0422\u0426\u041a \u041e\u0434\u0435\u0441\u0441\u0430 \u0448\u0442\u0443\u0440\u043c", "\u0422\u0440\u0430\u043c\u043f \u0436\u0435\u0440\u0442\u0432\u044b \u0423\u043a\u0440\u0430\u0438\u043d\u0430 \u043c\u0438\u0440\u043d\u043e\u0435 \u043d\u0430\u0441\u0435\u043b\u0435\u043d\u0438\u0435"]
for q in queries:
    r = requests.get('https://news.google.com/rss/search', params={'q': q, 'hl': 'ru', 'gl': 'RU', 'ceid': 'RU:ru'}, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    feed = feedparser.parse(r.content)
    print(f"query: {len(feed.entries)} entries")
    for e in feed.entries[:2]:
        print(f"  {e.get('title','')[:60]} | {e.get('published','')[:20]}")
