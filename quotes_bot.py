"""
🎌 Anime Quotes Bot — Бот с цитатами из аниме
AI автоматически генерирует реальные цитаты из аниме!
Публикует каждые 25 минут с артами
"""
import asyncio
import logging
import random
import aiohttp
import json
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
POST_INTERVAL_MINUTES = int(os.getenv("POST_INTERVAL_MINUTES", "30"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Инициализация бота
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# AI клиент (Groq - бесплатно!)
ai_client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
) if GROQ_API_KEY else None

# Список аниме для разнообразия
ANIME_LIST = [
    "Naruto",
    "Naruto Shippuden",
    "Boruto",
    "One Piece",
    "Bleach",
    "Dragon Ball Z",
    "Dragon Ball Super",
    "Attack on Titan",
    "Death Note",
    "Fullmetal Alchemist: Brotherhood",
    "Code Geass",
    "Steins;Gate",
    "Cowboy Bebop",
    "Neon Genesis Evangelion",
    "One Punch Man",
    "Mob Psycho 100",
    "Hunter x Hunter",
    "My Hero Academia",
    "Demon Slayer",
    "Jujutsu Kaisen",
    "Tokyo Ghoul",
    "Sword Art Online",
    "Re:Zero",
    "Konosuba",
    "No Game No Life",
    "Overlord",
    "That Time I Got Reincarnated as a Slime",
    "The Rising of the Shield Hero",
    "Vinland Saga",
    "Chainsaw Man",
    "Spy x Family",
    "Bocchi the Rock",
    "Kaguya-sama: Love is War",
    "Your Lie in April",
    "Clannad",
    "Anohana",
    "Violet Evergarden",
    "A Silent Voice",
    "Your Name",
    "Spirited Away",
    "Princess Mononoke",
    "Howl's Moving Castle",
    "Akira",
    "Ghost in the Shell",
    "Psycho-Pass",
    "Monster",
    "Parasyte",
    "Erased",
    "The Promised Neverland",
    "Made in Abyss",
    "Dororo",
    "Samurai Champloo",
    "Rurouni Kenshin",
    "Gintama",
    "Black Clover",
    "Fairy Tail",
    "Seven Deadly Sins",
    "Blue Exorcist",
    "Soul Eater",
    "D.Gray-man",
    "Noragami",
    "Bungo Stray Dogs",
    "Durarara",
    "Baccano",
    "91 Days",
    "Banana Fish",
    "Devilman Crybaby",
    "Hell's Paradise",
    "Frieren: Beyond Journey's End",
    "Oshi no Ko",
    "Solo Leveling",
    "Blue Lock",
    "Haikyuu",
    "Kuroko no Basket",
    "Slam Dunk",
    "Initial D",
    "Wangan Midnight",
    "JoJo's Bizarre Adventure",
    "Berserk",
    "Claymore",
    "Hellsing Ultimate",
    "Elfen Lied",
    "Mirai Nikki",
    "Another",
    "Higurashi",
    "Fate/Zero",
    "Fate/Stay Night",
    "Fate/Grand Order",
    "Monogatari Series",
    "March Comes in Like a Lion",
    "Mushishi",
    "Natsume's Book of Friends",
    "The Disastrous Life of Saiki K",
    "Nichijou",
    "K-On!",
    "Lucky Star",
    "Toradora",
    "Oregairu",
    "Horimiya",
    "Fruits Basket",
    "Ouran High School Host Club",
    "Maid Sama",
    "Kaichou wa Maid-sama",
    "Classroom of the Elite",
    "Assassination Classroom",
    "Great Teacher Onizuka",
    "Welcome to the NHK",
    "Serial Experiments Lain",
    "Texhnolyze",
    "Ergo Proxy",
    "Darker than Black",
    "Black Lagoon",
    "Jormungand",
    "Gate",
    "Log Horizon",
    "Grimgar of Fantasy and Ash",
    "Goblin Slayer",
    "Danmachi",
    "Mushoku Tensei",
    "86",
    "Vivy: Fluorite Eye's Song",
    "Wonder Egg Priority",
    "Odd Taxi",
    "Ranking of Kings",
    "Sonny Boy",
    "Cyberpunk: Edgerunners",
    "Pluto",
    "Dandadan",
]

# История использованных цитат (чтобы не повторяться)
used_quotes_history = []
MAX_HISTORY = 100

# Счётчик постов
posts_count = 0


async def generate_quote_with_ai(retry_count: int = 0) -> dict | None:
    """Генерация реальной цитаты из аниме через AI"""
    if not ai_client:
        logger.error("❌ GROQ_API_KEY не указан!")
        return None
    
    if retry_count >= 3:
        logger.error("❌ Превышено количество попыток генерации")
        return None
    
    try:
        # Выбираем случайное аниме
        anime = random.choice(ANIME_LIST)
        
        # Формируем запрос к AI
        prompt = f"""Напиши одну РЕАЛЬНУЮ, СУЩЕСТВУЮЩУЮ цитату из аниме "{anime}".

ВАЖНО:
- Цитата должна быть НАСТОЯЩЕЙ из аниме, не выдуманной
- Укажи персонажа, который её произносит (на русском и японском если знаешь)
- Цитата должна быть глубокой, философской, мотивирующей или запоминающейся
- Если не знаешь реальную цитату из этого аниме - выбери другое известное аниме

Ответь ТОЛЬКО валидным JSON без дополнительного текста:
{{
    "anime": "Название аниме",
    "character": "Имя персонажа",
    "quote": "Текст цитаты на русском",
    "quote_jp": "Оригинал на японском (если знаешь)",
    "context": "Краткий контекст (1 предложение)",
    "image_keywords": "ключевые слова для арта"
}}

ВАЖНО: JSON должен быть валидным! Без лишних скобок, запятых в конце, только чистый JSON!"""

        response = await ai_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты эксперт по аниме и манге. Отвечай только валидным JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.9,  # Высокая температура для разнообразия
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Извлекаем JSON
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]
        
        # Очищаем JSON от лишних символов
        result_text = result_text.strip()
        # Убираем лишние скобки в конце
        while result_text.endswith(')') or result_text.endswith(','):
            result_text = result_text.rstrip('),')
        # Находим первую { и последнюю }
        start = result_text.find('{')
        end = result_text.rfind('}')
        if start != -1 and end != -1 and end > start:
            result_text = result_text[start:end+1]
        
        # Пробуем исправить частые ошибки
        result_text = result_text.replace('",)', '")')  # Убираем лишние запятые перед скобками
        result_text = result_text.replace('",\n)', '"\n}')  # Исправляем закрывающие скобки
        
        quote_data = json.loads(result_text)
        
        # Проверяем что цитата не повторяется
        quote_key = f"{quote_data['anime']}:{quote_data['quote'][:50]}"
        if quote_key in used_quotes_history:
            logger.info("🔄 Цитата уже была, генерируем новую...")
            return await generate_quote_with_ai(retry_count=retry_count)
        
        # Добавляем в историю
        used_quotes_history.append(quote_key)
        if len(used_quotes_history) > MAX_HISTORY:
            used_quotes_history.pop(0)
        
        logger.info(f"✅ Сгенерирована цитата: {quote_data['anime']} - {quote_data['character']}")
        return quote_data
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка парсинга JSON: {e}")
        logger.error(f"   Ответ: {result_text[:200]}")
        # Пробуем исправить и распарсить ещё раз
        try:
            # Пробуем найти JSON вручную
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
            if json_match:
                fixed_json = json_match.group(0)
                quote_data = json.loads(fixed_json)
                logger.info("✅ JSON исправлен и распарсен!")
                
                # Проверяем что цитата не повторяется
                quote_key = f"{quote_data['anime']}:{quote_data['quote'][:50]}"
                if quote_key in used_quotes_history:
                    logger.info("🔄 Цитата уже была, генерируем новую...")
                    return await generate_quote_with_ai()
                
                used_quotes_history.append(quote_key)
                if len(used_quotes_history) > MAX_HISTORY:
                    used_quotes_history.pop(0)
                
                logger.info(f"✅ Сгенерирована цитата: {quote_data['anime']} - {quote_data['character']}")
                return quote_data
        except:
            pass
        
        # Если не получилось исправить - пробуем ещё раз
        logger.warning(f"⚠️ Попытка {retry_count + 1}/3: повторная генерация...")
        return await generate_quote_with_ai(retry_count=retry_count + 1)
    except Exception as e:
        logger.error(f"❌ Ошибка генерации цитаты: {e}")
        return None


async def get_anime_image(keywords: str, anime: str) -> bytes | None:
    """Получить РЕАЛЬНЫЙ арт из аниме (без генерации!)"""
    try:
        import urllib.parse
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            
            # Способ 1: Kitsu API (более стабильный)
            anime_query = urllib.parse.quote(anime)
            kitsu_url = f"https://kitsu.io/api/edge/anime?filter[text]={anime_query}&page[limit]=1"
            
            try:
                async with session.get(kitsu_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("data") and len(data["data"]) > 0:
                            anime_data = data["data"][0]["attributes"]
                            # Берём постер (оригинальный размер)
                            image_url = (
                                anime_data.get("posterImage", {}).get("original") or
                                anime_data.get("posterImage", {}).get("large") or
                                anime_data.get("coverImage", {}).get("original") or
                                anime_data.get("coverImage", {}).get("large")
                            )
                            if image_url:
                                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=20)) as img_resp:
                                    if img_resp.status == 200:
                                        logger.info(f"✅ Kitsu: найден арт для {anime}")
                                        return await img_resp.read()
            except Exception as e:
                logger.warning(f"Kitsu не сработал: {e}")
            
            # Способ 2: Jikan API (MyAnimeList) - запасной
            await asyncio.sleep(0.5)  # Небольшая задержка для API
            jikan_url = f"https://api.jikan.moe/v4/anime?q={anime_query}&limit=1"
            
            try:
                async with session.get(jikan_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("data") and len(data["data"]) > 0:
                            anime_data = data["data"][0]
                            image_url = anime_data.get("images", {}).get("jpg", {}).get("large_image_url")
                            if image_url:
                                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=20)) as img_resp:
                                    if img_resp.status == 200:
                                        logger.info(f"✅ Jikan: найден арт для {anime}")
                                        return await img_resp.read()
            except Exception as e:
                logger.warning(f"Jikan не сработал: {e}")
            
            logger.warning(f"⚠️ Не удалось найти арт для {anime}")
            return None
                    
    except Exception as e:
        logger.error(f"Ошибка получения картинки: {e}")
    
    return None


def format_quote_message(quote_data: dict) -> str:
    """Форматировать сообщение с цитатой"""
    # Основной текст
    text = f"""🎌 <b>{quote_data['anime']}</b>

<blockquote>«{quote_data['quote']}»</blockquote>

— <i>{quote_data['character']}</i>"""
    
    # Добавляем оригинал на японском если есть
    if quote_data.get('quote_jp') and quote_data['quote_jp'] != quote_data['quote']:
        text += f"\n\n🇯🇵 <i>«{quote_data['quote_jp']}»</i>"
    
    # Добавляем контекст если есть
    if quote_data.get('context'):
        text += f"\n\n💭 {quote_data['context']}"
    
    # Хэштеги
    anime_tag = quote_data['anime'].replace(' ', '').replace(':', '').replace('-', '').replace("'", '').replace("!", "")[:15]
    text += f"\n\n━━━━━━━━━━━━━━━\n#аниме #цитаты #{anime_tag}"
    
    return text


async def post_quote_to_channel() -> bool:
    """Опубликовать цитату в канал"""
    global posts_count
    
    if not CHANNEL_ID:
        logger.warning("⚠️ CHANNEL_ID не указан!")
        return False
    
    try:
        # Генерируем цитату через AI
        quote_data = await generate_quote_with_ai()
        
        if not quote_data:
            logger.error("❌ Не удалось сгенерировать цитату")
            return False
        
        message_text = format_quote_message(quote_data)
        
        logger.info(f"📤 Публикуем: {quote_data['anime']} - {quote_data['character']}")
        
        # Получаем картинку
        image_data = await get_anime_image(
            quote_data.get('image_keywords', ''),
            quote_data['anime']
        )
        
        if image_data:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=BufferedInputFile(image_data, filename="game_quote.png"),
                caption=message_text
            )
            logger.info("✅ Цитата с картинкой опубликована!")
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=message_text)
            logger.info("✅ Цитата опубликована (без картинки)")
        
        posts_count += 1
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка публикации: {e}")
        return False


async def scheduler():
    """Планировщик публикаций"""
    logger.info(f"⏰ Автопостинг запущен! Интервал: {POST_INTERVAL_MINUTES} минут")
    
    while True:
        try:
            await asyncio.sleep(POST_INTERVAL_MINUTES * 60)
            await post_quote_to_channel()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            await asyncio.sleep(60)


# ============ КОМАНДЫ ============

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Приветствие — направляем в канал"""
    # Игнорируем группы и каналы — отвечаем только в личке
    if message.chat.type != "private":
        return
    
    # Для админа показываем полное меню
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            f"""🎌 <b>Anime Quotes Bot</b> (Админ-панель)

📊 Опубликовано: <b>{posts_count}</b> цитат
🎯 Аниме в базе: <b>{len(ANIME_LIST)}+</b>

<b>Команды:</b>
/post — Опубликовать сейчас
/stats — Статистика
/quote — Тест цитаты
"""
        )
    else:
        # Для обычных пользователей — приглашаем в канал
        channel_link = CHANNEL_ID.replace("@", "") if CHANNEL_ID.startswith("@") else ""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎌 Подписаться на канал", url=f"https://t.me/{channel_link}")],
        ]) if channel_link else None
        
        await message.answer(
            f"""🎌 <b>Аниме цитаты</b>

Легендарные цитаты из аниме с красивыми артами!

Каждые <b>{POST_INTERVAL_MINUTES} минут</b> — новая цитата.

👇 <b>Подписывайся на канал:</b>""",
            reply_markup=keyboard
        )


@dp.message(Command("quote"))
async def cmd_quote(message: types.Message):
    """Получить случайную цитату — только для админа в личке"""
    # Игнорируем группы
    if message.chat.type != "private":
        return
    
    # Только админ может тестировать
    if message.from_user.id != ADMIN_ID:
        channel_link = CHANNEL_ID.replace("@", "") if CHANNEL_ID.startswith("@") else ""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎌 Смотреть цитаты", url=f"https://t.me/{channel_link}")],
        ]) if channel_link else None
        await message.answer(
            "🎌 Все цитаты публикуются в канале!\n\n👇 Подписывайся:",
            reply_markup=keyboard
        )
        return
    
    if not ai_client:
        await message.answer("❌ GROQ_API_KEY не указан в .env!")
        return
    
    status = await message.answer("🎮 Генерирую цитату...")
    
    quote_data = await generate_quote_with_ai()
    
    if not quote_data:
        await status.edit_text("😔 Не удалось сгенерировать цитату. Попробуй ещё раз!")
        return
    
    await status.edit_text("🎨 Загружаю картинку...")
    
    message_text = format_quote_message(quote_data)
    image_data = await get_anime_image(
        quote_data.get('image_keywords', ''),
        quote_data['anime']
    )
    
    await status.delete()
    
    if image_data:
        await message.answer_photo(
            photo=BufferedInputFile(image_data, filename="quote.png"),
            caption=message_text
        )
    else:
        await message.answer(message_text)


@dp.message(Command("post"))
async def cmd_post(message: types.Message):
    """Опубликовать сейчас — только в личке"""
    if message.chat.type != "private":
        return
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Только для администратора")
        return
    
    if not CHANNEL_ID:
        await message.answer("❌ CHANNEL_ID не указан в .env!")
        return
    
    status = await message.answer("📤 Публикую в канал...")
    success = await post_quote_to_channel()
    
    if success:
        await status.edit_text("✅ Опубликовано!")
    else:
        await status.edit_text("❌ Ошибка. Проверь настройки.")


@dp.message(Command("anime"))
async def cmd_anime(message: types.Message):
    """Список аниме — только для админа в личке"""
    if message.chat.type != "private":
        return
    if message.from_user.id != ADMIN_ID:
        return  # Игнорируем
    anime_text = ", ".join(ANIME_LIST[:30])
    await message.answer(
        f"🎌 <b>Аниме в базе ({len(ANIME_LIST)} шт):</b>\n\n{anime_text}..."
    )


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Статистика — только для админа в личке"""
    if message.chat.type != "private":
        return
    if message.from_user.id != ADMIN_ID:
        return  # Игнорируем
    await message.answer(
        f"""📊 <b>Статистика</b>

🎌 Аниме в базе: {len(ANIME_LIST)}
📝 Опубликовано: {posts_count}
🔄 В истории: {len(used_quotes_history)} цитат

⏰ Интервал: {POST_INTERVAL_MINUTES} мин
📢 Канал: {CHANNEL_ID or 'не указан'}
🤖 AI: {'✅ Подключен' if ai_client else '❌ Не настроен'}
"""
    )


@dp.message()
async def handle_any_message(message: types.Message):
    """Любое другое сообщение — направляем в канал (только в личке!)"""
    # Игнорируем всё кроме личных сообщений
    if message.chat.type != "private":
        return
    
    if message.from_user.id == ADMIN_ID:
        return  # Админа не трогаем
    
    channel_link = CHANNEL_ID.replace("@", "") if CHANNEL_ID.startswith("@") else ""
    if channel_link:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Перейти в канал", url=f"https://t.me/{channel_link}")],
        ])
        await message.answer(
            "🎮 Я только публикую цитаты в канале.\n\n👇 Подписывайся!",
            reply_markup=keyboard
        )


# ============ ЗАПУСК ============

async def main():
    """Запуск бота"""
    logger.info("🎌 Anime Quotes Bot запускается...")
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не указан!")
        return
    
    if not GROQ_API_KEY:
        logger.error("❌ GROQ_API_KEY не указан!")
        logger.error("   Получи бесплатный ключ на https://console.groq.com")
        return
    
    if not CHANNEL_ID:
        logger.warning("⚠️ CHANNEL_ID не указан — автопостинг отключен")
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем планировщик
    scheduler_task = asyncio.create_task(scheduler())
    
    # Первая публикация
    if CHANNEL_ID:
        logger.info("📤 Первая публикация...")
        await post_quote_to_channel()
    
    logger.info("✅ Бот запущен!")
    
    try:
        await dp.start_polling(bot)
    finally:
        scheduler_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
