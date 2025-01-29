import discord
import logging
import requests
import os
import mysql.connector
import datetime

from dotenv import load_dotenv
from discord.ext import commands
from dateutil.relativedelta import relativedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

load_dotenv(".env", override=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0"
}

class CTFTimes(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def ctf_information(self, ctx: discord.ApplicationContext, guild: discord.Guild, event_id: str):
        """
        Fetch and display CTF information.
        """
        try:
            response = requests.get(
                f"https://ctftime.org/api/v1/events/{event_id}/", headers=HEADERS
            )
            response.raise_for_status()
            info = response.json()

            title = info["title"]
            url = info["url"]
            start = info["start"]
            end = info["finish"]
            description = info["description"]
            weight = info["weight"]
            onsite = info["onsite"]
            format_type = f"{'Online' if not onsite else 'Offline'} {info['format']}"

            image = info["logo"] if info["logo"] else "https://play-lh.googleusercontent.com/uiZnC5tIBpejW942OXct4smbaHmSowdT5tLSi28Oeb2_pMLPCL-VJqdGIH6ZO3A951M=w480-h960"

            start_ts = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z").timestamp()
            end_ts = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z").timestamp()

            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.blue(),
                url=url,
            )
            embed.set_thumbnail(url=image)
            embed.add_field(name="URL", value=url, inline=False)
            embed.add_field(name="Start", value=f"<t:{int(start_ts)}:f>", inline=False)
            embed.add_field(name="End", value=f"<t:{int(end_ts)}:f>", inline=False)
            embed.add_field(name="CTF Weight", value=weight, inline=False)
            embed.add_field(name="Format", value=format_type, inline=False)
            
            await ctx.respond(embed=embed)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching CTF information: {e}")
            await ctx.respond("An error occurred while fetching the CTF information.", ephemeral=True)
        except ValueError as e:
            logging.error(f"Error decoding JSON response: {e}")
            await ctx.respond("An error occurred while decoding the JSON response.", ephemeral=True)


    async def upcoming_ctf(self, ctx: discord.ApplicationContext, guild: discord.Guild):
        now = datetime.datetime.utcnow().timestamp()
        next_week = datetime.datetime.utcnow() + relativedelta(days=+7)
        future = next_week.timestamp()
        try:
            response = requests.get(
                f"https://ctftime.org/api/v1/events/?limit=5&start={int(now)}&finish={int(future)}",
                headers=HEADERS
            )
            response.raise_for_status()
            info = response.json()

            embed = discord.Embed(
                title="Upcoming CTF Events",
                description="Here are the upcoming CTF events in the next 7 days.",
                color=discord.Color.blue()
            )

            for event in info:
                name = event["title"]
                url = event["url"]
                start = event["start"]
                event_id = event["id"]

                # Parse the start date
                start_dt = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
                start_ts = int(start_dt.timestamp())

                embed.add_field(name=name, value=f"[Link]({url})", inline=True)
                embed.add_field(name="Event ID", value=event_id, inline=True)
                embed.add_field(name="Start Date", value=f"<t:{start_ts}:f>", inline=True)

            await ctx.respond(embed=embed)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching upcoming CTF events: {e}")
            await ctx.respond("An error occurred while fetching the upcoming CTF events.", ephemeral=True)
        except ValueError as e:
            logging.error(f"Error decoding JSON response: {e}")
            await ctx.respond("An error occurred while decoding the JSON response.", ephemeral=True)
            
    
    @commands.slash_command(
        name="ctf-upcoming",
        description="Get upcoming CTF events",
    )
    async def ctfupcoming(self, ctx: discord.ApplicationContext):
        """
        Command to fetch upcoming CTF events.
        """
        guild = ctx.guild
        await self.upcoming_ctf(ctx, guild)
        

    @commands.slash_command(
        name='ctf-info',
        description='Find more information about the CTF event',
    )
    async def ctfinfo(self, ctx: discord.ApplicationContext, event_id: str):
        """
        Command to fetch CTF information.
        """
        guild = ctx.guild
        await self.ctf_information(ctx, guild, event_id)
    
    
    # @commands.slash_command(
    #     name='ctf-contest-room',
    #     description='Create channel with topic for CTFd contest',
    # )
    # @commands.has_permissions(manage_channels=True)
    # async def ctfcontestroom(self, ctx: discord.ApplicationContext, event_id: str, api_key: str):
    #     """
    #     Command to create a channel with a topic for a CTFd contest.
    #     """
    #     try:
    #         guild = ctx.guild
    #         response = requests.get(
    #             f"https://ctftime.org/api/v1/events/{event_id}/", headers=HEADERS
    #         )
    #         response.raise_for_status()
    #         info = response.json()
    #         title = info["title"]
    #         category = discord.utils.get(guild.categories, name="CTFd 🚩")
    #         if category is None:
    #             category = await guild.create_category("CTFd 🚩")
    #         await guild.create_text_channel(title, category=category)
            
    #         # for category in categories:
    #         #     await guild.send(category, category=category)
    #         await ctx.respond(f"Created a channel for the CTFd contest: {title}", ephemeral=True)
    #     except requests.exceptions.RequestException as e:
    #         logging.error(f"Error fetching CTF information: {e}")
    #         await ctx.respond("An error occurred while fetching the CTF information.", ephemeral=True)
    #     except ValueError as e:
    #         logging.error(f"Error decoding JSON response: {e}")
    #         await ctx.respond("An error occurred while decoding the JSON response.", ephemeral=True)    
    
    @commands.slash_command(
        name='ctf-room',
        description='Create channel with topic for CTFd contest',
    )
    @commands.bot_has_permissions(manage_channels=True, manage_roles=True)
    @commands.has_role('Admin')
    async def create(self, ctx, ctf_name):
        try:
            
        except Exception as e:
            await ctx.send(e)
            return
        # category = discord.utils.get(ctx.guild.categories, name=ctf_name)
        # if category is None:
        #     await ctx.guild.create_category(name=ctf_name)
        #     category = discord.utils.get(ctx.guild.categories, name=ctf_name)
        #     await category.set_permissions(ctx.guild.me, read_messages=True, send_messages=True, speak=True)

        # if ctf_name[0] == '-':
        #     ctf_name = ctf_name[1:]

        # while '--' in ctf_name:
        #     ctf_name = ctf_name.replace('--', '-')

        # role = await ctx.guild.create_role(name=ctf_name, mentionable=True)
        # channel = await ctx.guild.create_text_channel(name="Main", category=category)
        # await channel.set_permissions(ctx.guild.default_role, read_messages=False)
        # await channel.set_permissions(role, read_messages=True)
        # await ctx.message.add_reaction("✅")
        
def setup(bot):
    bot.add_cog(CTFTimes(bot))
    
