import logging
import re
from typing import Dict, Optional

import discord
from discord.ext import commands

from config import (
    CHATBOT_WHITELIST,
    CHATBOT_ENABLED
)
import google.generativeai as genai

from google.generativeai.types.generation_types import (
    BlockedPromptException,
    StopCandidateException
)

ADMIN_USER_ID = 295188325684346880
TARGET_SERVER_ID = 1216978943920443452
TARGET_CHANNEL_ID = 1308319389397028884

TRAINING_LINKS: Dict[str, Dict[str, str]] = {
    "System_Training": {
        "1": "<https://drive.google.com/file/d/1MCBXsXGmOIUjkcMDsMVFPzl9Pbofo78y/view?usp=sharing>",
    },
    "Network_Training": {
        "1": "<https://drive.google.com/file/d/17z6ZdA2Ifpv493mXaoWp69g12onLhoDP/view?usp=sharing>",
    },
    "Code_Training": {
        "1": "<https://drive.google.com/file/d/1beiwBbvLLYN8N1eruH67wWHRgqMp9uvL/view?usp=sharing>",
    }
}

PATTERNS = {
    "system": re.compile(r"^-(?P<username>\w+)_<Day_(?P<day>\d+)_System_Record>$"),
    "network": re.compile(r"^-(?P<username>\w+)_<Day_(?P<day>\d+)_Network_Record>$"),
    "code": re.compile(r"^-(?P<username>\w+)_<Day_(?P<day>\d+)_Code_Record>$")
}

async def handle_record_request(
    bot: commands.Bot, 
    message: discord.Message
) -> Optional[bool]:
    """
    Handle record link requests based on message content.
    Supports both server and DM contexts.
    """
    for pattern_type, training_type in [
        ("system", "System"),
        ("network", "Network"),
        ("code", "Code")
    ]:
        match = PATTERNS[pattern_type].match(message.content)
        if match:
            username = match.group("username")
            day = match.group("day")

            # Delete the original message in a server context
            if message.guild:
                await message.delete()

            # Notify admin
            try:
                admin_user = await bot.fetch_user(ADMIN_USER_ID)
                if admin_user:
                    await admin_user.send(f"User {message.author} requested {training_type} training record for day {day}.")
            except discord.Forbidden:
                logging.warning(f"Could not DM admin about {training_type} record request.")

            # Check and send link
            links = TRAINING_LINKS.get(f"{training_type}_Training", {})
            if day in links:
                try:
                    await message.author.send(
                        f"Chào bạn {username}, record {training_type} của buổi {day} của bạn đây nha: {links[day]}"
                    )
                except discord.Forbidden:
                    await message.channel.send(
                        f"Bạn {message.author.mention} ơi, mình không thể gửi riêng cho bạn được á, Kiểm tra lại cài đặt của mình nha."
                    )

                # Send notification to the target channel in the target server
                if message.guild:  # Server context only
                    target_server = bot.get_guild(TARGET_SERVER_ID)
                    if target_server:
                        target_channel = target_server.get_channel(TARGET_CHANNEL_ID)
                        if target_channel:
                            await target_channel.send(
                                f"User {message.author} requested {training_type} training record for day {day}. The link has been sent."
                            )
                        else:
                            logging.error(f"Target channel with ID {TARGET_CHANNEL_ID} not found.")
                    else:
                        logging.error(f"Target server with ID {TARGET_SERVER_ID} not found.")
            else:
                await message.channel.send(
                    f"kohane.err.rec-404 | あれれ？{message.author.mention}さん, mình không thể tìm thấy record bạn cần đó. Hãy hỏi lại các khầy phụ trách hoặc chọn lại ngày nha."
                )
            return True
    return None

if CHATBOT_ENABLED:
    from bot.chatbot.gemini import Gembot, active_chats

    class Chatbot(commands.Cog):
        def __init__(self, bot) -> None:
            self.bot = bot

        @commands.slash_command(
            name="reset_chatbot",
            description="Resets the chatbot."
        )
        async def reset_chatbot(self, ctx: discord.ApplicationContext) -> None:
            Gembot(ctx.guild_id)
            await ctx.respond("Done!")

        @commands.Cog.listener()
        async def on_message(self, message: discord.Message) -> None:
            # Ignore messages from the bot itself
            if message.author == self.bot.user:
                return

            # Handle record requests
            record_handled = await handle_record_request(self.bot, message)
            if record_handled:
                return

            # Chatbot interaction logic
            server_id = message.guild.id if message.guild else message.author.id  # Use author ID for DM interactions
            if server_id not in active_chats:
                active_chats[server_id] = Gembot(server_id)
            
            chat = active_chats[server_id]
            if await chat.is_interacting(message):
                async with message.channel.typing():
                    try:
                        params = await chat.get_params(message)
                        reply = await chat.send_message(*params)
                        formatted_reply = chat.format_reply(reply)
                        await message.channel.send(formatted_reply)

                        await chat.memory.store(
                            params[0],
                            author=message.author.name,
                            id=server_id,
                        )
                    except StopCandidateException:
                        await message.channel.send("*filtered*")
                    except BlockedPromptException:
                        logging.error("Blocked prompt!")

else:
    class Chatbot(commands.Cog):
        def __init__(self, bot) -> None:
            self.bot = bot

def setup(bot):
    bot.add_cog(Chatbot(bot))