# -*- coding: utf-8 -*-
from pathlib import Path
content = Path('publication/formatter.py').read_text(encoding='utf-8-sig')
old = '''    post_url = post.original_url or f"https://t.me/{post.source_channel}"
    lines.append(f"Пост: {_link(post_url, post_url)}")'''
new = '''    post_url = post.original_url or f"https://t.me/{post.source_channel}"
    lines.append(f"Пост: {_link(post_url, post_url)}")
    lines.append(f"ID: #{post.event_id}")'''
if old in content:
    content = content.replace(old, new)
    Path('publication/formatter.py').write_text(content, encoding='utf-8')
    print('ok')
else:
    print('not found')
