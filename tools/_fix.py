# -*- coding: utf-8 -*-
from pathlib import Path
content = Path('verification/llm_verifier.py').read_text(encoding='utf-8-sig')
old = '''    user_prompt = (
        "Утверждения:\\n"
        + "\\n".join(f"ID {claim['id']}: {claim['text']}" for claim in claims)
        + "\\n\\nИсточники (полный текст):\\n"
        + "\\n\\n".join(
            f"=== SOURCE ID {source['id']} ===\\nDomain: {source.get('domain', '')}\\nTitle: {source.get('title', '')}\\nText:\\n{source.get('text', '')}"
            for source in sources
        )
        + "\\n\\nВерни вердикты по схеме. ВАЖНО: quote должен быть ТОЧНОЙ подстрокой из поля Text источника."
    )'''
new = '''    user_prompt = (
        "Утверждения:\\n"
        + "\\n".join(f"ID {claim['id']}: {claim['text']}" for claim in claims)
        + "\\n\\nИсточники (полный текст, с датой публикации):\\n"
        + "\\n\\n".join(
            f"=== SOURCE ID {source['id']} ===\\nDomain: {source.get('domain', '')}\\nTitle: {source.get('title', '')}\\nPublished: {source.get('published_at', 'unknown')}\\nText:\\n{source.get('text', '')}"
            for source in sources
        )
        + "\\n\\nВерни вердикты по схеме. ВАЖНО:\\n1. quote должен быть ТОЧНОЙ подстрокой из поля Text источника.\\n2. Источник подтверждает утверждение ТОЛЬКО если описывает ТОТ ЖЕ САМЫЙ инцидент/событие, а не похожее другое событие в другое время.\\n3. Если источник описывает другой случай (даже похожий) — это UNCONFIRMED, не CONFIRMED."
    )'''
if old in content:
    content = content.replace(old, new)
    Path('verification/llm_verifier.py').write_text(content, encoding='utf-8')
    print('ok')
else:
    print('not found')
