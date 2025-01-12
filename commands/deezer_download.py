import asyncio
import os
import discord
import boto3
import logging

from dotenv import load_dotenv
from discord.ext import commands
from deezer.errors import DataException
from botocore.exceptions import BotoCoreError, ClientError
from bot.utils import cleanup_cache, tag_flac_file, get_cache_path

load_dotenv('.env')
DEEZER_ENABLED = bool(os.getenv('DEEZER_ENABLED'))
UPLOAD_TO_S3_ENABLED = bool(os.getenv('UPLOAD_TO_S3_ENABLED'))

end_url = os.getenv(ENDPOINT_URL)

r2_client = boto3.client(
    's3',
    endpoint_url=end_url,
    aws_access_key_id=os.getenv("AWS_SECRET_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY")
)

class DeezerDownload(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(
        name='dzdl',
        description='Tải bài hát chất lượng cao từ Deezer.',
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        }
    )
    async def dzdl(
        self,
        ctx: discord.ApplicationContext,
        query: str
    ) -> None:
        if not DEEZER_ENABLED:
            await ctx.respond(content='Tính năng Deezer chưa được bật.')
            return

        await ctx.respond('Chờ mình một lát nha~')

        # Get the track from query
        self.bot.downloading = True
        try:
            track = await self.bot.deezer.get_stream_url_from_query(query)
        except DataException:
            await ctx.edit(content="Không tìm thấy bài hát !")
            return
        if not track:
            await ctx.edit(content="Không tìm thấy bài hát !")
            return

        # Set the cache path
        cleanup_cache()
        file_path = get_cache_path(str(track['track_id']).encode('utf-8'))

        # Download
        if not file_path.is_file():
            file_path = await asyncio.to_thread(self.bot.deezer.download, track)

        # Tag the file
        display_name = f"{track['artist']} - {track['title']}"
        await tag_flac_file(
            file_path,
            title=track['title'],
            date=track['date'],
            artist=track['artists'],
            album=track['album'],
            album_cover_url=track['cover']
        )

        # Upload if possible
        size = os.path.getsize(file_path)
        if size < ctx.guild.filesize_limit:
            await ctx.edit(
                content="Của bạn đây !",
                file=discord.File(
                    file_path,
                    filename=f"{display_name}.flac"
                )
            )
        elif UPLOAD_TO_S3_ENABLED:
            try:
                bucket_name = os.getenv("BUCKET_NAME")
                display_name_link = display_name.replace(' ','%20')
                key = f"{bucket_name}/tracks/{display_name}.flac" # Tên tệp khi ở trên xô S3
                key_link = f"{bucket_name}tracks/{display_name_link}.flac" # Tên tệp được chỉnh sửa để phù hợp với cấu trúc đường dẫn URL

                r2_client.upload_file(file_path, bucket_name, key)

                custom_domain = os.getenv("CUSTOM_DOMAIN")
                if custom_domain:
                    public_url = f"{custom_domain}/{key_link}"
                else:
                    public_url = f"{end_url}/{key_link}"

                await ctx.edit(content=f"Tệp quá lớn. Bạn có thể tải tại đây: {public_url}")
            except (BotoCoreError, ClientError) as e:
                logging.error(f"Error uploading to S3: {e}")
                await ctx.edit(content="Tải thất bại. Không thể tải lên S3")
        else:
            await ctx.edit(content="Tải thất bại: Tệp quá lớn")


def setup(bot):
    bot.add_cog(DeezerDownload(bot))