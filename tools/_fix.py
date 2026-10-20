# -*- coding: utf-8 -*-
from pathlib import Path
content = Path('web/queries.py').read_text(encoding='utf-8-sig')
content = content.replace(
    '"events_needs_check": "SELECT COUNT(*) FROM events WHERE current_status=\'ТРЕБУЕТ ДОДОЛНИТЕЛЬНОЙ ПРОВЕРКИ\'"',
    '"events_needs_check": "SELECT COUNT(*) FROM events WHERE current_status LIKE \'%ПРОВЕРК%\'"'
)
Path('web/queries.py').write_text(content, encoding='utf-8')
print('ok')
