import discord
import os

from dotenv import load_dotenv
from discord.ext import commands


load_dotenv('.env')
CHATBOT_ENABLED = bool(os.getenv('CHATBOT_ENABLED'))
SPOTIFY_ENABLED = bool(os.getenv('SPOTIFY_ENABLED'))


class HelpDropdown(discord.ui.Select):
    def __init__(self):
        
        options = [ #base options
            discord.SelectOption(
                label="Khác",
                description="Các tính năng khác",
                emoji="🌀"
            )
        ]
        
        if SPOTIFY_ENABLED:
            options.insert(0,
                discord.SelectOption(
                    label="Music Bot",
                    description="Bot nghe nhạc",
                    emoji="🎵"
                )
            )
        if CHATBOT_ENABLED:
            options.insert(1,
                discord.SelectOption(
                    label="Chatbot / LLM",
                    description="Chatbot / LLM",
                    emoji="🤖"
                )
            )
        super().__init__(
            placeholder="Chọn một danh mục...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        """Hàm callback khi người dùng chọn một tùy chọn từ dropdown."""
        selected = self.values[0]

        if selected == "Music Bot":
            embed = discord.Embed(
                title="Lệnh Bot Nhạc",
                description="Chỉ hoạt động trên máy chủ!",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="/play",
                value=(
                    "Phát bài hát / danh sách phát / album (Spotify, Deezer, YouTube hoặc Onsei)\n"
                    "Ví dụ: ``/play Bức Tường Tháng 12``\n"
                ),
                inline=False
            )
            embed.add_field(
                name="/shuffle",
                value="Trộn ngẫu nhiên / hủy trộn hàng đợi\n",
                inline=False
            )
            embed.add_field(
                name="/loop",
                value="Lặp lại / ngừng lặp lại hàng đợi\n",
                inline=False
            )
            embed.add_field(
                name="/clear",
                value="Xóa hàng đợi hiện tại và dừng bài hát\n",
                inline=False
            )
            embed.add_field(
                name="/leave",
                value="Thoát khỏi kênh thoại hiện tại\n",
                inline=False
            )
            embed.add_field(
                name="/lyrics",
                value=(
                    "Lấy lời bài hát hiện tại hoặc bất kỳ bài hát nào\n"
                    "Ví dụ: ``/lyrics Bức Tường Tháng 12 English``\n"
                ),
                inline=False
            )
            embed.add_field(
                name="/pause",
                value="Tạm dừng bài hát hiện tại\n",
                inline=False
            )
            embed.add_field(
                name="/resume",
                value="Tiếp tục bài hát hiện tại\n",
                inline=False
            )
            embed.add_field(
                name="/seek",
                value=(
                    "Chuyển đến vị trí bất kỳ trong bài hát (giây)\n"
                    "Ví dụ: ``/seek 60``\n"
                ),
                inline=False
            )
            embed.add_field(
                name="/previous",
                value="Phát bài hát trước đó\n",
                inline=False
            )
            embed.add_field(
                name="/skip",
                value="Bỏ qua bài hát hiện tại\n",
                inline=False
            )
            embed.add_field(
                name="/spdl",
                value=(
                    "Tải bài hát từ Spotify\n"
                    "Ví dụ: ``/spdl https://open.spotify.com/track/0JoasWonl4e716Nh1eQ06m``\n"
                ),
                inline=False
            )
            embed.add_field(
                name="/dzdl",
                value=(
                    "Tải bài hát từ Deezer\n"
                    "Ví dụ: ``/dzdl 24/7 Shining``\n"
                ),
                inline=False
            )

        elif selected == "Chatbot / LLM":
            embed = discord.Embed(
                title="Lệnh Chatbot / LLM",
                color=discord.Color.green()
            )
            embed.add_field(
                name="/ask",
                value=(
                    "Hỏi Kohane bất kỳ điều gì\n"
                    "Ví dụ: ``/ask Viết một đoạn mã Python hiển thị thời gian hiện tại``\n"
                    "Hoạt động trên: Máy chủ / Cá nhân"
                ),
                inline=False
            )
            embed.add_field(
                name="/summarize",
                value=(
                    "Tóm tắt văn bản hoặc video YouTube\n"
                    "Ví dụ: ``/summarize https://www.youtube.com/watch?v=Km2DNLbB-6o``\n"
                    "Hoạt động trên: Máy chủ / Cá nhân"
                ),
                inline=False
            )
            embed.add_field(
                name="/reset_chatbot",
                value=(
                    "Đặt lại lịch sử chatbot. Không xóa các mục Pinecone\n"
                    "Ví dụ: ``/reset_chatbot``\n"
                    "Hoạt động trên: Máy chủ / Cá nhân"
                ),
                inline=False
            )
            embed.add_field(
                name="/translate",
                value=(
                    "Dịch bất kỳ nội dung nào sang ngôn ngữ khác\n"
                    "Ví dụ: ``/translate ミン・トゥさんはだいすきです``\n"
                    "Hoạt động trên: Máy chủ / Cá nhân"
                ),
                inline=False
            )
            embed.add_field(
                name="!",
                value=(
                    "Kích hoạt chatbot\n"
                    "Ví dụ: ``!Hi, bạn là ai?``\n"
                    "Hoạt động trên: Máy chủ"
                ),
                inline=False
            )
            embed.add_field(
                name="!!",
                value=(
                    "Kích hoạt chế độ liên tục của chatbot\n"
                    "Ví dụ: ``!!Hi, bạn là ai?``\n"
                    "Hoạt động trên: Máy chủ"
                ),
                inline=False
            )

        else:  # "Khác"
            embed = discord.Embed(
                title="Lệnh Khác",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="Record",
                value=(
                    "Lấy link record từ một buổi training bất kỳ\n"
                    "Ví dụ: ``-Hikari_<Day_1_Code_Record>``\n"
                    "Hoạt động trên: Máy chủ / Cá nhân"
                ),
                inline=False
            )

            embed.add_field(
                name="/ping",
                value=(
                    "Kiểm tra thời gian phản hồi của Kohane! \n"
                    "Ví dụ: ``/ping``\n"
                    "Hoạt động trên: Máy chủ / Cá nhân"
                ),
                inline=False
            )
            embed.add_field(
                name="/get-stickers",
                value=(
                    "Tải bất kỳ bộ sticker nào từ Line\n"
                    "Ví dụ: ``/get-stickers https://store.line.me/stickershop/product/28492189/en``\n"
                    "Hoạt động trên: Máy chủ / Cá nhân"
                ),
                inline=False
            )
            embed.add_field(
                name="/echo",
                value=(
                    "Lặp lại tin nhắn của bạn\n"
                    "Ví dụ: ``/echo Don't be afraid to find us, we are here to secure your digital life``\n"
                    "Hoạt động trên: Máy chủ / Cá nhân"
                ),
                inline=False
            )
            embed.add_field(
                name="/danbooru",
                value=(
                    "Lấy hình ảnh từ bất kỳ thẻ nào trên danbooru (ảnh thân thiện với gia đình)\n"
                    "Ví dụ: ``/danbooru nanashi_mumei``\n"
                    "Hoạt động trên: Máy chủ / Cá nhân"
                ),
                inline=False
            )

        # Cập nhật tin nhắn gốc với embed mới
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpDropdown())


class Help(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(
        name="help",
        description="Hiển thị menu trợ giúp."
    )
    async def help_command(self, ctx: discord.ApplicationContext) -> None:
        """Hiển thị menu trợ giúp."""
        embed = discord.Embed(
            title="Menu Trợ Giúp",
            description="Chọn một danh mục từ dropdown bên dưới.",
            color=discord.Color.blurple()
        )
        view = HelpView()
        await ctx.respond(
            embed=embed,
            view=view,
            ephemeral=True
        )


def setup(bot):
    bot.add_cog(Help(bot))