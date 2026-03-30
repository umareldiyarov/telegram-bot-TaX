import os
import time
import asyncio
import hashlib
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

async def cleanup_hashes():
    while True:
        await asyncio.sleep(300)
        now = time.time()
        expired = [k for k, v in sent_hashes.items() if now - v > DUPLICATE_TIME]
        for k in expired:
            del sent_hashes[k]

@client.on(events.NewMessage(chats=SOURCE_GROUP))
async def handler(event):
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

    key = hashlib.md5(text.encode()).hexdigest()
    now = time.time()
    if key in sent_hashes and now - sent_hashes[key] < DUPLICATE_TIME:
        return
    sent_hashes[key] = now

    await client.forward_messages(TARGET_GROUP, event.message)
    print(f"✅ Заявка переслана!")

async def main():
    await client.start()
    print("✅ Бот запущен!")
    asyncio.create_task(cleanup_hashes())
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
