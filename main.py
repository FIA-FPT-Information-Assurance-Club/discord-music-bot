import discord
import os
import logging
import asyncio

from pathlib import Path
from bot.vocal.spotify import SpotifySessions, Spotify
from bot.vocal.youtube import Youtube
from dotenv import load_dotenv

load_dotenv(".env")

BOT_TOKEN = os.getenv('BOT_TOKEN')
DEV_TOKEN = os.getenv('DEV_TOKEN')
SPOTIFY_API_ENABLED = bool(os.getenv('SPOTIFY_API_ENABLED'))
CHATBOT_ENABLED = bool(os.getenv('CHATBOT_ENABLED'))
DEEZER_ENABLED = bool(os.getenv('DEEZER_ENABLED'))
COMMANDS_FOLDER = Path('./commands')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME')

if CHATBOT_ENABLED:
    from bot.chatbot.vector_recall import memory

if DEEZER_ENABLED:
    from bot.vocal.deezer import Deezer_

# Init bot
intents = discord.Intents.default()
intents.message_content = True
loop = asyncio.get_event_loop()
bot = discord.Bot(intents=intents, loop=loop)


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

    if CHATBOT_ENABLED:
        logging.error("Chatbot enabled")
        await memory.init_pinecone(PINECONE_INDEX_NAME)
    bot.youtube = Youtube()


for filepath in COMMANDS_FOLDER.rglob('*.py'):
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