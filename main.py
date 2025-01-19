import discord
import os
import logging
import asyncio

from pathlib import Path
from bot.vocal.spotify import SpotifySessions, Spotify
from bot.vocal.youtube import Youtube
from dotenv import load_dotenv

load_dotenv(".env",override=True)

BOT_TOKEN = os.getenv('BOT_TOKEN')
DEV_TOKEN = os.getenv('DEV_TOKEN')

SPOTIFY_API_ENABLED = os.getenv('SPOTIFY_API_ENABLED','false').strip().lower() == "true"
CHATBOT_ENABLED = os.getenv('CHATBOT_ENABLED').strip().lower() == "true"
DEEZER_ENABLED = os.getenv('DEEZER_ENABLED').strip().lower() == "true"
COMMANDS_FOLDER = Path('./commands')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME')

if CHATBOT_ENABLED:
    from bot.chatbot.vector_recall import memory

if DEEZER_ENABLED:
    from bot.vocal.deezer import Deezer_

intents = discord.Intents.default()
intents.message_content = True
loop = asyncio.get_event_loop()
bot = discord.Bot(intents=intents, loop=loop)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


@bot.event
async def on_ready() -> None:
    logging.info(f"{bot.user} is running !")
    if SPOTIFY_API_ENABLED:
        spotify_sessions = SpotifySessions()
        spotify = Spotify(spotify_sessions)
        await spotify_sessions.init_spotify()
        bot.downloading = False
        bot.spotify = spotify
        if DEEZER_ENABLED:
            logging.error("Deezer enabled")
            bot.deezer = Deezer_()
            await bot.deezer.init_deezer()
    else:
        logging.error("Deezer disabled")

    if CHATBOT_ENABLED:
        print("Chatbot enabled")
        logging.info("Chatbot enabled")
        await memory.init_pinecone(PINECONE_INDEX_NAME)
    else:
        logging.info("Chatbot disabled")
    bot.youtube = Youtube()


for filepath in COMMANDS_FOLDER.rglob('*.py'):
    if filepath.name == "__init__.py":
        continue

    relative_path = filepath.relative_to(COMMANDS_FOLDER).with_suffix('')
    module_name = f"commands.{relative_path.as_posix().replace('/', '.')}"
    logging.info(f'Loading {module_name}')
    bot.load_extension(module_name)


async def start() -> None:
    await bot.start(DEV_TOKEN)

try:
    loop.run_until_complete(start())
finally:
    if not bot.is_closed():
        loop.run_until_complete(bot.close())