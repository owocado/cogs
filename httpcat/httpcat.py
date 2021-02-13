import aiohttp
from io import BytesIO
from typing import Any, Dict, Literal

# Required by Red
import discord
from redbot.core import checks, commands
from redbot.core.bot import Red

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class HTTPCat(commands.Cog):
    """Various commands to show the stats about users' profile badges."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.0.3"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot: Red):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload():
        self.bot.loop.create_task(self.session.close())

    # credits to jack1142
    async def red_get_data_for_user(self, *, user_id: int) -> Dict[str, Any]:
        # this cog does not story any data
        return {}

    # credits to jack1142
    async def red_delete_data_for_user(
        self, *, requester: RequestType, user_id: int
    ) -> None:
        # this cog does not story any data
        pass

    @commands.guild_only()
    @commands.command(aliases=["hcat"])
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def httpcat(self, ctx: commands.Context, code: int):
        """Responds with HTTP cat image for given error code."""
        async with ctx.typing():
            async with self.session.get(f"https://http.cat/{code}") as resp:
                if resp.status == 200:
                    data = BytesIO(await resp.read())
                    data.name = "httpcat.jpg"
                    data.seek(0)
                    file = discord.File(data)
                    return await ctx.send(file=file)
                else:
                    await ctx.send(f"Received response code: {resp.status}")

    @commands.guild_only()
    @commands.command(aliases=["hdog"])
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def httpdog(self, ctx: commands.Context, code: int):
        """Responds with HTTP dog image for given error code."""
        async with ctx.typing():
            link = f"https://httpstatusdogs.com/img/{code}.jpg"
            async with self.session.get(link) as resp:
                if resp.status == 200:
                    data = BytesIO(await resp.read())
                    data.name = "httpdog.jpg"
                    data.seek(0)
                    file = discord.File(data)
                    return await ctx.send(file=file)
                else:
                    await ctx.send(f"Received response code: {resp.status}")

    @commands.guild_only()
    @commands.command(aliases=["hduck"])
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def httpduck(self, ctx: commands.Context, code: int):
        """Responds with HTTP duck image for given error code."""
        async with ctx.typing():
            link = f"https://random-d.uk/api/http/{code}.jpg"
            async with self.session.get(link) as resp:
                if resp.status == 200:
                    data = BytesIO(await resp.read())
                    data.name = "httpduck.jpg"
                    data.seek(0)
                    file = discord.File(data)
                    return await ctx.send(file=file)
                else:
                    await ctx.send(f"Received response code: {resp.status}")
