import logging
import discord
import os

from dotenv import load_dotenv
from typing import Optional
from discord.ext import commands
from bot.lyrics import BotLyrics
from bot.vocal.session_manager import session_manager
from bot.utils import get_dominant_rgb_from_url, split_into_chunks
from commands.vocal.play import Play


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


load_dotenv('.env', override=True)
SPOTIFY_ENABLED = os.getenv('SPOTIFY_ENABLED', 'false').lower() == 'true'
DEFAULT_EMBED_COLOR = tuple(os.getenv('DEFAULT_EMBED_COLOR'))
CHATBOT_ENABLED = os.getenv('CHATBOT_ENABLED', 'false').lower() == 'true'

class Lyrics(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(
        name="lyrics",
        description='Lấy lời bài hát bất kỳ, hoặc bài hát đang phát hiện tại.'
    )
    async def lyrics(
        self,
        ctx: discord.ApplicationContext,
        query: Optional[str],
        convert_to: discord.Option(
            str,
            choices=[
                'Romaji',
                'Japanese Kana',
                'English',
                'Japanese',
                'French'
            ],
            required=False
        )  # type: ignore
        # Uncomment the following if Spotify features are disabled
        # artist: str = Optional[str]
    ) -> None:
        if not query:
            guild_id = ctx.guild.id
            session = session_manager.server_sessions.get(guild_id)

            if session and session.queue:
                track_info = session.queue[0]['track_info']
            else:
                await ctx.respond('Không có bài hát đang phát !')
                return
        else:
            if SPOTIFY_ENABLED:
                # Use Spotify features for more precise results
                tracks_info = await self.bot.spotify.get_tracks(query)

                if not tracks_info:
                    await ctx.respond('Không tìm thấy lời bài hát!')
                    return
                track_info = tracks_info[0]
            else:
                track_info = {
                    'title': query,
                    # Uncomment the following if Spotify features are disabled
                    # 'artist': artist
                }

        lyrics = await BotLyrics.get(track_info)
        if not lyrics:
            await ctx.respond(lyrics or 'Không tìm thấy lời bài hát!')
            return

        # CONVERT
        if convert_to:
            if not CHATBOT_ENABLED:
                await ctx.respond(
                    'Tính năng chatbot phải được bật để '
                    'sử dụng tính năng chuyển đổi lời bài hát.'
                )
                return
            await ctx.respond('Đang chuyển đổi~')
            lyrics = await BotLyrics.convert(lyrics, convert_to)

        # Split the lyrics in case it's too long
        splitted_lyrics: list = split_into_chunks(lyrics)

        # Create the embed
        if 'cover' in track_info:
            dominant_rgb = await get_dominant_rgb_from_url(track_info['cover'])
            color = discord.Colour.from_rgb(*dominant_rgb)
        else:
            color = discord.Colour.from_rgb(*DEFAULT_EMBED_COLOR)
        embed = discord.Embed(
            title=track_info.get('display_name', query),
            color=color
        )
        for part in splitted_lyrics:
            embed.add_field(name='', value=part, inline=False)

        if SPOTIFY_ENABLED:
            # Create the view if Spotify enabled (buttons)
            class lyricsView(discord.ui.View):
                def __init__(
                    self,
                    bot: discord.bot,
                    ctx: discord.ApplicationContext
                ) -> None:
                    super().__init__(timeout=None)
                    self.bot = bot
                    self.ctx = ctx

                    spotify_button = discord.ui.Button(
                        label="Spotify Link",
                        style=discord.ButtonStyle.link,
                        url=track_info['url']
                    )
                    self.add_item(spotify_button)

                @discord.ui.button(
                    label="Phát ngay",
                    style=discord.ButtonStyle.primary,
                )
                async def play_button_callback(
                    self,
                    button: discord.ui.Button,
                    interaction: discord.Interaction
                ) -> None:
                    play_cog: Play = self.bot.get_cog('Play')
                    await play_cog.execute_play(
                        ctx,
                        track_info['url'], 'Spotify',
                        interaction
                    )

            # Add a cover to the embed
            embed.set_author(name="Lời bài hát", icon_url=track_info['cover'])

            await ctx.respond(embed=embed, view=lyricsView(self.bot, ctx))
        else:
            await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Lyrics(bot))
