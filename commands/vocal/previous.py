import discord

from discord.ext import commands
from bot.vocal.session_manager import session_manager as sm
from bot.vocal.server_session import *
from bot.utils import send_response


class Previous(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def execute_previous(
        self,
        ctx: discord.ApplicationContext,
        send: bool = False
    ) -> None:
        guild_id: int = ctx.guild.id
        session: Optional[ServerSession] = sm.server_sessions.get(guild_id)
        respond = (ctx.send if send else ctx.respond)

        if not session:
            await send_response(
                respond,
                "Không có phiên hoạt động",
                guild_id
            )
            return

        if not session.stack_previous:
            await send_response(
                respond,
                "Không có bài hát nào phát trước đó!",
                guild_id
            )
            return

        await send_response(
            respond,
            "Đang phát bài hát trước!",
            guild_id
        )
        await session.play_previous(ctx)

    @commands.slash_command(
        name='previous',
        description='Phát bài hát trước.'
    )
    async def previous(self, ctx: discord.ApplicationContext) -> None:
        await self.execute_previous(ctx)


def setup(bot):
    bot.add_cog(Previous(bot))
