import discord
import logging
import requests
import os
import datetime
import json

from dotenv import load_dotenv
from discord.ext import commands
from dateutil.relativedelta import relativedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

load_dotenv(".env", override=True)
CTF_VERIFICATION_ROLE_ID = os.getenv("CTF_VERIFICATION_ROLE_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0"
}

class CTFTimes(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.ctf_role_id = int(CTF_VERIFICATION_ROLE_ID)

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
            

    async def send_join_ctf_message(self, channel: discord.TextChannel, event_id: str):  
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

            await channel.send(embed=embed)

            embed = discord.Embed(
                title="Join CTF",
                description="React ✅ this message to join the CTF event.",
                color=discord.Color.green()
            )
            message = await channel.send(embed=embed)
            await message.add_reaction("✅")
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching CTF information: {e}")
            await channel.send("An error occurred while fetching the CTF information.")
        except ValueError as e:
            logging.error(f"Error decoding JSON response: {e}")
            await channel.send("An error occurred while decoding the JSON response.")

                            
    def check_ctf_information(self, event_id:str):
        """
        Check if the event ID is valid.
        """
        try:
            response = requests.get(
                f"https://ctftime.org/api/v1/events/{event_id}/", headers=HEADERS
            )
            response.raise_for_status()
            info = response.json()
            return True, info['title']
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching CTF information: {e}")
            return False, None
        except ValueError as e:
            logging.error(f"Error decoding JSON response: {e}")
            return False, None

    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """
        Assign the CTF role when a user reacts with ✅.
        """
        if user.bot:
            return

        if reaction.emoji == "✅" and reaction.message.author == self.bot.user:
            guild = reaction.message.guild
            ctf_role = guild.get_role(self.ctf_role_id)
            if ctf_role:
                await user.add_roles(ctf_role, reason="Joined CTF event")
                logging.info(f"Assigned {ctf_role.name} to {user.name}")
                
                category = reaction.message.channel.category
                logs_channel = discord.utils.get(category.channels, name="logs")
                
                if logs_channel:
                    await logs_channel.send(f"Add {ctf_role.name} from {user.mention}")
                else:
                    logging.info("Logs channel not found in the category!")
            else:
                logging.info("CTF role not found!")


    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        """
        Remove the CTF role when a user removes their ✅ reaction and log the action.
        """
        if user.bot:
            return

        if reaction.emoji == "✅" and reaction.message.author == self.bot.user:
            guild = reaction.message.guild
            ctf_role = guild.get_role(self.ctf_role_id)
            
            if ctf_role:    
                await user.remove_roles(ctf_role, reason="Left CTF event")
                logging.info(f"Removed {ctf_role.name} from {user.mention}")

                category = reaction.message.channel.category
                logs_channel = discord.utils.get(category.channels, name="logs")
                
                if logs_channel:
                    await logs_channel.send(f"Removed {ctf_role.name} from @{user.name}")
                else:
                    logging.info("Logs channel not found in the category!")
            else:
                logging.info("CTF role not found!")
                
                
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
    
        
    @commands.slash_command(
    name='ctf-room',
    description='Create channel with topic for CTFd contest',
    )
    @commands.bot_has_permissions(manage_channels=True, manage_roles=True)
    @commands.has_role('Admin')
    async def create(self, ctx, event_id):
        try:
            exist, ctf_name = self.check_ctf_information(event_id)
            if exist and ctf_name:
                category_name = f'{ctf_name} 🚩'
                category = discord.utils.get(ctx.guild.categories, name=category_name)
                
                if not category:
                    category = await ctx.guild.create_category(category_name)
                    
                    normal_perm = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True, read_message_history = True),
                    }

                    join_ctf_channel = await ctx.guild.create_text_channel(name='join-ctf', category=category, overwrites=normal_perm)
                    
                    await self.send_join_ctf_message(join_ctf_channel, event_id)
                    
                    ctf_perm = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, read_message_history = True),
                        ctx.guild.get_role(self.ctf_role_id): discord.PermissionOverwrite(read_messages=True, read_message_history = True)
                    }
                    
                    challenge_channel = await ctx.guild.create_text_channel(name='challenges', category=category, overwrites=ctf_perm)
                    general_channel = await ctx.guild.create_text_channel(name='general', category=category, overwrites=ctf_perm)
                    embed = discord.Embed(
                        title=f"{ctf_name}",
                        description=f"Current and deploy challenges of {ctf_name}. To add challenges, please use command `/challenge` in #general, if you solve the challenge, use `/solve` in that thread, if create by mistake the challange, please use `delete` in the thread.",
                        color=discord.Color.green()
                    )
                    await challenge_channel.send(embed=embed)
                    admin_role = discord.utils.get(ctx.guild.roles, name='Admin')
                    admin_perm = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        admin_role: discord.PermissionOverwrite(read_messages=True)
                    }
                    
                    await ctx.guild.create_text_channel(name='logs', category=category, overwrites=admin_perm)
                    
                    await ctx.respond(f"Created category: {category_name}", ephemeral=True)
                else:
                    await ctx.respond("Category already exists", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"Error: {str(e)}", ephemeral=True)


    @commands.slash_command(
        name='challenges',
        description='Create a thread for the challenge in the CTF event',
    )
    @commands.has_any_role(CTF_VERIFICATION_ROLE_ID, 'Admin')
    async def challenge(self, ctx: discord.ApplicationContext, challenge_category: str, challenge_name: str):
        if ctx.channel.name != "general":
            await ctx.respond("Please use this command in the #general channel only.", ephemeral=True)
            return

        category = ctx.channel.category
        if not category:
            await ctx.respond("This channel doesn't belong to a category!", ephemeral=True)
            return

        general_channel = discord.utils.get(category.channels, name="general")
        challenge_channel = discord.utils.get(category.channels, name="challenges")

        if not general_channel:
            await ctx.respond("The #general channel doesn't exist in this category!", ephemeral=True)
            return

        if not challenge_channel:
            await ctx.respond("The #challenges channel doesn't exist in this category!", ephemeral=True)
            return

        existing_thread = discord.utils.find(
            lambda t: t.name == f"{challenge_category}/{challenge_name}", general_channel.threads
        )

        if existing_thread:
            await ctx.respond(f"A thread for this challenge already exists: {existing_thread.jump_url}", ephemeral=True)
            return

        await ctx.respond(f"Creating thread for challenge: {challenge_name}", ephemeral=True)
        thread = await general_channel.create_thread(
            name=f"{challenge_category}/{challenge_name}",
            type=discord.ChannelType.public_thread
        )

        await ctx.send(f"Challenge created: {thread.jump_url}")

        embed = None
        target_message = None

        async for message in challenge_channel.history(limit=100):
            if message.embeds and message.embeds[0].title == "Challenges":
                embed = message.embeds[0]
                target_message = message
                break

        if not embed:
            embed = discord.Embed(
                title="Challenges",
                color=discord.Color.green()
            )

        category_field = None
        for field in embed.fields:
            if field.name == challenge_category:
                category_field = field
                break

        if category_field:
            updated_value = f"{category_field.value}\n{challenge_name} → {thread.jump_url}"
            embed.set_field_at(embed.fields.index(category_field), name=category_field.name, value=updated_value, inline=False)
        else:
            embed.add_field(
                name=f"{challenge_category}",
                value=f"{challenge_name} → {thread.jump_url}",
                inline=False
            )

        if target_message:
            await target_message.edit(embed=embed)
        else:
            await challenge_channel.send(embed=embed)




    @commands.slash_command(
        name='solve',   
        description='Mark the challenge as solved',
    )
    @commands.has_any_role(CTF_VERIFICATION_ROLE_ID, 'Admin')
    async def solve(self, ctx: discord.ApplicationContext):
        await ctx.send("Solved the challenge")
    
    @commands.slash_command(
        name='delete',
        description='Delete the challenge',
    )
    @commands.has_any_role(CTF_VERIFICATION_ROLE_ID, 'Admin')
    async def delete(self, ctx: discord.ApplicationContext):
        await ctx.send("Deleted the challenge")
        
def setup(bot):
    bot.add_cog(CTFTimes(bot))
    
