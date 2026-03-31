import os
import time
import asyncio
import hashlib
import random
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SOURCE_GROUP = int(os.getenv("SOURCE_GROUP"))
TARGET_GROUP = int(os.getenv("TARGET_GROUP"))
DUPLICATE_TIME = int(os.getenv("DUPLICATE_TIME", 60))
STRING_SESSION = os.getenv("STRING_SESSION") 

client = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH,
    sequential_updates=False,
    connection_retries=-1,
    auto_reconnect=True,
)

sent_hashes = {}

# Списки городов (вынесли из обработчика для скорости)
bishkek = ["бишкек", "bishkek", "биш"]
issyk_kol = [
    "каракол", "балыкчы", "чолпон", "чолпон-ата", "чолпон ата",
    "бостери", "боостери", "тамчы", "кара-ой", "кара ой", "долинка", 
    "чок-тал", "чок тал", "сары-ой", "сары ой", "орнок", "булан-соготту", 
    "корумду", "темирканат", "ананьево", "тору-айгыр", "боконбаево", 
    "каджи-сай", "каджи сай", "тамга", "кызыл-туу", "ак-терек", "тон",
    "кызыл-суу", "покровка", "джети-огуз", "липенка", "саруу", "дархан",
    "ак-суу", "тюп", "жыргалан", "иссык", "issyk", "ыссык-кол", "ыссык-куль"
]

@client.on(events.NewMessage(chats=SOURCE_GROUP))
async def handler(event):
    # 1. Симуляция "Сна" (Бот не работает с 2 до 6 утра)
    hour = datetime.now().hour
    if 2 <= hour <= 6:
        return

    text = event.message.text
    if not text:
        return

    text_lower = text.lower()
    if "пассажир" not in text_lower:
        return

    def contains_any(words):
        return any(w in text_lower for w in words)

    if not (contains_any(bishkek) and contains_any(issyk_kol)):
        return

    # 2. Проверка дублей
    key = hashlib.md5(text.encode()).hexdigest()
    now = time.time()
    if key in sent_hashes and now - sent_hashes[key] < DUPLICATE_TIME:
        return
    sent_hashes[key] = now

    # 3. РАНДОМНАЯ ЗАДЕРЖКА (имитация чтения)
    # Вместо 0 секунд делаем от 10 до 25 секунд.
    delay = random.randint(1, 5)
    
    # Запускаем отправку в фоне, чтобы не тормозить прием новых сообщений
    asyncio.create_task(copy_message(event.message, delay))

async def copy_message(message, delay):
    try:
        await asyncio.sleep(delay)
        
        # 4. ОТПРАВКА ТЕКСТОМ (без плашки "Переслано")
        # Это самое важное для защиты от админов-источников
        await client.send_message(
            TARGET_GROUP, 
            message.text, 
            buttons=message.buttons # Кнопки "Позвонить" останутся!
        )
        print(f"✅ Заявка скопирована (пауза {delay}с)")
    except Exception as e:
        print(f"[ошибка]: {e}")

async def main():
    await client.start()
    print("🚀 Бот запущен в режиме 'НЕВИДИМКА'")
    
    # Очистка хешей раз в 10 минут
    async def cleanup():
        while True:
            await asyncio.sleep(600)
            now = time.time()
            expired = [k for k, t in sent_hashes.items() if now - t > DUPLICATE_TIME]
            for k in expired:
                del sent_hashes[k]
    
    asyncio.create_task(cleanup())
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
