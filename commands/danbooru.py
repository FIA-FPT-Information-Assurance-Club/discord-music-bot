import logging
import discord

from httpx._exceptions import HTTPStatusError
from discord.ext import commands
from bot.danbooru import Danbooru
from bot.utils import get_dominant_rgb_from_url
from bot.search import is_url

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


class Danbooru_(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.danbooru = Danbooru()

    @commands.slash_command(
        name="danbooru",
        description='Lấy một ảnh bất kỳ từ một tag trên danbooru (ảnh phù hợp với gia đình)',
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    async def danbooru_(
        self,
        ctx: discord.ApplicationContext,
        tag: discord.Option(
            str,
            autocomplete=Danbooru.autocomplete
        )  # type: ignore
    ) -> None:
        await ctx.defer()
        try:
            posts = await self.danbooru.get_posts(
                tag=tag,
                limit=10
            )
        except HTTPStatusError as e:
            logging.error(f"Failed to get posts from {tag}: {e}")
            await ctx.respond(f"Không thể láy bài đăng từ {tag}.")
            return
        if not posts:
            await ctx.respond("Không tìm thấy bài đăng !")
            return

        sent = False
        for i in range(len(posts)):
            # Variables
            post: dict = posts[i]
            id: int = post.get('id', 0)
            url: str = post.get('file_url', '')
            rating: str = post.get('rating', '')
            # e: explicit, q: questionable
            if not url or rating in {'e', 'q', ''}:
                continue
            source = post.get('source', '')
            danbooru_source = f"https://danbooru.donmai.us/posts/{id}"
            if is_url(source):
                desc = (f"[nguồn]({source}), "
                        f"[nguồn danbooru]({danbooru_source})")
            else:
                desc = f"[nguồn danbooru]({danbooru_source})"

            # Prepare the embed
            dominant_rgb = await get_dominant_rgb_from_url(post['preview_file_url'])
            color = discord.Colour.from_rgb(*dominant_rgb)
            embed = discord.Embed(
                description=desc,
                color=color
            ).set_author(
                name=tag.replace('_', ' '),
                icon_url="https://danbooru.donmai.us/packs/static/danbooru-logo-128x128-ea111b6658173e847734.png"
            ).set_image(
                url=url
            ).set_footer(
                text=post.get('tag_string_artist', '').replace('_', ' ')
            )

            await ctx.respond(embed=embed)
            sent = True
            break

        if not sent:
            await ctx.respond('Không thể tìm bài đăng !')


def setup(bot):
    bot.add_cog(Danbooru_(bot))
