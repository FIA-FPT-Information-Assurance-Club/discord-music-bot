import discord
import os

from dotenv import load_dotenv
from typing import Optional
from discord.ext import commands
from bot.vocal.session_manager import session_manager as sm
from bot.vocal.server_session import ServerSession
from bot.vocal.audio_source_handlers import play_spotify, play_custom, play_onsei, play_youtube
from bot.utils import is_onsei, send_response
from bot.search import is_url

load_dotenv('.env', override=True)
SPOTIFY_ENABLED = os.getenv('SPOTIFY_ENABLED','false').lower() == 'true'
DEEZER_ENABLED = os.getenv('DEEZER_ENABLED','false').lower() == 'true'
SPOTIFY_API_ENABLED = os.getenv('SPOTIFY_API_ENABLED','false').lower() == 'true'
DEFAULT_STREAMING_SERVICE = os.getenv('DEFAULT_STREAMING_SERVICE')


class Play(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def execute_play(
        self,
        ctx: discord.ApplicationContext,
        query: str,
        source: str,
        interaction: Optional[discord.Interaction] = None,
        offset: int = 0,
    ) -> None:
        if interaction:
            respond = interaction.response.send_message
            edit = interaction.edit_original_response
        else:
            respond = ctx.respond
            edit = ctx.edit

        # Connect to the voice channel
        session: Optional[ServerSession] = await sm.connect(ctx, self.bot)
        if not session:
            await respond('Bạn không ở trong kênh thoại')
            return

        await send_response(respond, "Chờ mình một lát nha~", session.guild_id)

        source = source.lower()
        youtube_domains = ['youtube.com', 'www.youtube.com', 'youtu.be']
        spotify_domains = ['open.spotify.com']

        # Detect if the query refers to an Onsei
        if source == 'onsei' or is_onsei(query):
            await play_onsei(ctx, query, session)

        # If the query is custom or an URL not from Spotify/Youtube
        elif (source == 'custom'
              or (is_url(query)
                  and not is_url(query,
                                 from_=spotify_domains+youtube_domains))):
            await play_custom(ctx, query, session)

        # Else, search Spotify or Youtube
        elif (source == 'youtube'
              or is_url(query, from_=youtube_domains)):
            await play_youtube(ctx, query, session, interaction)

        elif source == 'spotify':
            if not SPOTIFY_ENABLED or not SPOTIFY_API_ENABLED:
                await edit(
                    content=('API Spotify hoặc tính năng Spotify chưa được bật.')
                )
                return

            await play_spotify(ctx, query, session, interaction, 'Spotify', offset)

        # If deezer is chosen as a source, a lossless audio stream source 
        # will be injected before playing the track 
        # (start_playing function in server_session)
        elif source == 'deezer':
            if not SPOTIFY_API_ENABLED or not DEEZER_ENABLED:
                await edit(
                    content=('API Spotify hoặc tính năng Deezer chưa được bật.')
                )
                return

            await play_spotify(ctx, query, session, interaction, 'Deezer', offset)

        else:
            await edit(content='wut duh')

    @commands.slash_command(
        name='play',
        description='Chọn bài hát để phát.'
    )
    async def play(
        self,
        ctx: discord.ApplicationContext,
        query: str,
        source: discord.Option(
            str,
            description="Dịch vụ phát trực tuyến mà bạn muốn dùng.",
            choices=['Deezer', 'Spotify', 'Youtube', 'Custom', 'Onsei'],
            default=DEFAULT_STREAMING_SERVICE
        ),  # type: ignore
        playlist_offset: discord.Option(
            int,
            description="Nếu yêu cầu của bạn là một danh sách nhạc, chọn bài hát để bắt đầu. Mặc định là 0.",
            default=0
        )  # type: ignore
    ) -> None:
        await self.execute_play(ctx, query, source, offset=playlist_offset)


def setup(bot):
    bot.add_cog(Play(bot))