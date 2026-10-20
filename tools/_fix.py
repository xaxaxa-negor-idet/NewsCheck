# -*- coding: utf-8 -*-
from pathlib import Path

content = Path('tools/publish.py').read_text(encoding='utf-8-sig')

old = '''        # Extract first real photo (skip emojis)
        import json as json_mod
        media_url = None
        media_kind = "photo"
        try:
            media_list = json_mod.loads(event["media"]) if event["media"] else []
            for m in media_list:
                if isinstance(m, str) and ".mp4" in m:
                    media_url = str(m)
                    media_kind = "video"
                    break
            if not media_url:
                for m in media_list:
                    if isinstance(m, str) and ("cdn" in m or m.endswith((".jpg", ".jpeg", ".png"))):
                        if m.startswith("//"):
                            m = "https:" + m
                        media_url = str(m)
                        media_kind = "photo"
                        break
        except (json_mod.JSONDecodeError, TypeError):
            pass'''

new = '''        # Fetch FRESH media URL from live t.me page (DB urls may be stale/truncated)
        media_url, media_kind = fetch_fresh_media(event["source_url"] or "")
        if not media_url:
            # Fallback: DB media
            import json as json_mod
            try:
                media_list = json_mod.loads(event["media"]) if event["media"] else []
                for m in media_list:
                    if isinstance(m, str) and ".mp4" in m:
                        media_url = str(m)
                        media_kind = "video"
                        break
                if not media_url:
                    for m in media_list:
                        if isinstance(m, str) and ("cdn" in m or m.endswith((".jpg", ".jpeg", ".png"))):
                            if m.startswith("//"):
                                m = "https:" + m
                            media_url = str(m)
                            media_kind = "photo"
                            break
            except (json_mod.JSONDecodeError, TypeError):
                pass'''

if old in content:
    content = content.replace(old, new)
    content = content.replace(
        'from publication.telegram import TelegramChannelDestination',
        'from search.media_fetcher import fetch_fresh_media\nfrom publication.telegram import TelegramChannelDestination'
    )
    # also fix the kind var below
    content = content.replace(
        '''        if media_url:
            kind = 'photo'
            if media_url.endswith(('.mp4', '.mov', '.avi')):
                kind = 'video'
            from publication.telegram import RenderedPostWithMedia
            rendered = RenderedPostWithMedia(
                event_id=post.event_id, text=rendered, media_url=media_url, media_kind=kind
            )''',
        '''        if media_url:
            from publication.telegram import RenderedPostWithMedia
            rendered = RenderedPostWithMedia(
                event_id=post.event_id, text=rendered, media_url=media_url, media_kind=media_kind
            )'''
    )
    Path('tools/publish.py').write_text(content, encoding='utf-8')
    print('ok')
else:
    print('not found')
