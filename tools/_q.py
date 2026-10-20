# -*- coding: utf-8 -*-
import requests
# check the post that had betting link (msg 102 = topor 53149)
r = requests.get('https://t.me/topor/53149?embed=1', timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
from bs4 import BeautifulSoup
soup = BeautifulSoup(r.text, 'html.parser')
text_el = soup.select_one('.tgme_widget_message_text')
if text_el:
    links = text_el.find_all('a')
    print('links in post:', len(links))
    for a in links:
        print(f"  href={a.get('href', '')[:70]} text={a.get_text()[:30]}")
else:
    print('no text element')
