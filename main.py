import os
import time
import asyncio
import hashlib
from pathlib import Path
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv

# 1. Загрузка настроек
load_dotenv(Path(__file__).parent / ".env")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SOURCE_GROUP = int(os.getenv("SOURCE_GROUP"))
TARGET_GROUP = int(os.getenv("TARGET_GROUP"))
DUPLICATE_TIME = int(os.getenv("DUPLICATE_TIME", 60))
STRING_SESSION = os.getenv("STRING_SESSION")

# 2. Инициализация клиента
client = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH,
    sequential_updates=False, # Чтобы обрабатывать сообщения параллельно
    connection_retries=-1,
    auto_reconnect=True,
)

sent_hashes = {}

# 3. Списки городов (вынесены для скорости)
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

# 4. Фоновая задача для очистки старых хешей (чтобы не тормозить основной поток)
async def cleanup_hashes():
    while True:
        await asyncio.sleep(300) # Чистим раз в 5 минут
        now = time.time()
        expired = [k for k, v in sent_hashes.items() if now - v > DUPLICATE_TIME]
        for k in expired:
            del sent_hashes[k]
        if expired:
            print(f"🧹 Очистка: удалено {len(expired)} дублей.")

# 5. Функция быстрой отправки
async def fast_forward(message):
    try:
        await client.forward_messages(TARGET_GROUP, message)
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

# 6. Основной обработчик
@client.on(events.NewMessage(chats=SOURCE_GROUP))
async def handler(event):
    text = event.message.text
    if not text:
        return

    text_lower = text.lower()

    # Фильтр на пассажира
    if "пассажир" not in text_lower:
        return

    # Проверка городов
    if not (any(w in text_lower for w in bishkek) and any(w in text_lower for w in issyk_kol)):
        return

    # Проверка на дубликаты
    key = hashlib.md5(text.encode()).hexdigest()
    now = time.time()

    if key in sent_hashes and now - sent_hashes[key] < DUPLICATE_TIME:
        return

    sent_hashes[key] = now

    # МОЛНИЕНОСНЫЙ ПУСК (не ждем ответа, кидаем в фон)
    asyncio.create_task(fast_forward(event.message))
    print(f"🚀 Заявка отправлена в очередь пересылки!")

async def main():
    await client.start()
    print("🔥 ГИБРИД ЗАПУЩЕН! Максимальная скорость + стабильность.")
    # Запускаем чистку хешей в фоне
    asyncio.create_task(cleanup_hashes())
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
