from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from bot.vocal.session_manager import session_manager as sm
from bot.vocal.server_session import ServerSession
from bot.utils import send_response


class Pause(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def execute_pause(
        self,
        ctx: discord.ApplicationContext,
        send: bool = True
    ) -> None:
        guild_id = ctx.guild.id
        session: Optional[ServerSession] = sm.server_sessions.get(guild_id)

        respond = (ctx.send if send else ctx.respond)

        if not session:
            await send_response(
                respond,
                "Không có bài hát được phát!",
                guild_id
            )
            return

        voice_client = session.voice_client

        if not voice_client or not voice_client.is_connected():
            await send_response(
                respond,
                "Kohane chưa được kết nối vào kênh thoại.",
                guild_id
            )
            return

        if not voice_client.is_playing():
            await send_response(
                respond,
                "Không có âm thanh được phát!",
                guild_id
            )
            return

        # Pause
        voice_client.pause()
        current_time = datetime.now()
        elapsed_time = (current_time - session.last_played_time).seconds
        session.time_elapsed += elapsed_time
        session.last_played_time = current_time

        await send_response(
            respond,
            f"Tạm ngưng vào {session.time_elapsed} giây!",
            guild_id
        )

    @commands.slash_command(
        name='pause',
        description='Tạm dừng bài hát hiện tại.'
    )
    async def execute(self, ctx: discord.ApplicationContext) -> None:
        await self.execute_pause(ctx, send=False)


def setup(bot):
    bot.add_cog(Pause(bot))
