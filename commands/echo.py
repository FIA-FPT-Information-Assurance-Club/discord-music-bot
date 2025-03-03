from discord.ext import commands

import discord
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class Echo(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @discord.slash_command(
        name='echo',
        description='Phát lại tin nhắn bất kỳ !',
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        },
    )
    async def echo(
        self,
        ctx: discord.ApplicationContext,
        message
    ) -> None:
        logging.info(f'{ctx.author.name} used /echo.')
        if not ctx.guild.me:
            await ctx.respond(content=message)
        else:
            await ctx.send(content=message)

def setup(bot):
    bot.add_cog(Echo(bot))
