import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('.env').resolve())
from openai import OpenAI

client = OpenAI(api_key=os.getenv('LLM_API_KEY'), base_url='https://tokify.sale/v1')
news = "В Москве на Садовом кольце произошло ДТП с участием трёх автомобилей, один человек погиб"
prompt = 'Извлеки из новости событие и 2 проверяемых утверждения. Ответ строго JSON: {"title": "...", "claims": ["...", "..."]}\nНовость: ' + news
completion = client.chat.completions.create(
    model='claude-opus-5.5',
    messages=[
        {'role': 'system', 'content': 'Ты — парсер новостей. Отвечай строго валидным JSON без пояснений.'},
        {'role': 'user', 'content': prompt},
    ],
    max_tokens=500,
)
content = completion.choices[0].message.content
print(content)
print('len:', len(content))
