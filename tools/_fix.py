# -*- coding: utf-8 -*-
from pathlib import Path
content = Path('core/pipeline.py').read_text(encoding='utf-8-sig')
old = '''            search_results = _fresh
'''
new = '''            search_results = _fresh

            # Relevance gate: source must match THIS event (not a lookalike from another day)
            from search.relevance import same_incident_keywords as _same_inc
            _relevant = []
            for source in search_results:
                if _same_inc(source.get("title", ""), source.get("text", ""), event_data["title"]):
                    _relevant.append(source)
            if _relevant:
                search_results = _relevant
'''
if old in content:
    content = content.replace(old, new, 1)
    Path('core/pipeline.py').write_text(content, encoding='utf-8')
    print('ok')
else:
    print('anchor not found')
