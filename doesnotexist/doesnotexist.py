import aiohttp
import random

from io import BytesIO
from typing import Any, Dict, Literal

# Required by Red
import discord
from redbot.core import checks, commands
from redbot.core.bot import Red

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class DoesNotExist(commands.Cog):
    """Various commands to show the stats about users' profile badges."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.0.7"

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
    @commands.command(aliases=["aiart"])
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def aiartwork(self, ctx: commands.Context):
        """Responds with randomly AI generated artwork."""
        async with ctx.typing():
            async with self.session.get("https://thisartworkdoesnotexist.com/") as resp:
                if resp.status == 200:
                    data = BytesIO(await resp.read())
                    data.name = "ai-artwork.jpg"
                    data.seek(0)
                    file = discord.File(data)
                    return await ctx.send(file=file)
                else:
                    await ctx.send(f"API returned status code: {resp.status}")

    @commands.guild_only()
    @commands.command(aliases=["aikitty"])
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def aicat(self, ctx: commands.Context):
        """Responds with randomly AI generated cat."""
        async with ctx.typing():
            async with self.session.get("https://thiscatdoesnotexist.com/") as resp:
                if resp.status == 200:
                    data = BytesIO(await resp.read())
                    data.name = "ai-kitty.jpg"
                    data.seek(0)
                    file = discord.File(data)
                    return await ctx.send(file=file)
                else:
                    await ctx.send(f"API returned status code: {resp.status}")

    @commands.guild_only()
    @commands.command(aliases=["aifurry"])
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def aifursona(self, ctx: commands.Context):
        """Responds with randomly AI generated furry persona."""
        async with ctx.typing():
            rint = random.randint(0, 99999)
            link = f"http://thisfursonadoesnotexist.com/v2/jpgs/seed{rint}.jpg"
            async with self.session.get(link) as resp:
                if resp.status == 200:
                    data = BytesIO(await resp.read())
                    data.name = "ai-fursona.jpg"
                    data.seek(0)
                    file = discord.File(data)
                    return await ctx.send(file=file)
                else:
                    await ctx.send(f"API returned status code: {resp.status}")

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def aihorse(self, ctx: commands.Context):
        """Responds with randomly AI generated horse."""
        async with ctx.typing():
            async with self.session.get("https://thishorsedoesnotexist.com/") as resp:
                if resp.status == 200:
                    data = BytesIO(await resp.read())
                    data.name = "ai-horse.jpg"
                    data.seek(0)
                    file = discord.File(data)
                    return await ctx.send(file=file)
                else:
                    await ctx.send(f"API returned status code: {resp.status}")

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def aiperson(self, ctx: commands.Context):
        """Responds with randomly AI generated human face."""
        async with ctx.typing():
            async with self.session.get("https://thispersondoesnotexist.com/image") as resp:
                if resp.status == 200:
                    data = BytesIO(await resp.read())
                    data.name = "ai-person.jpg"
                    data.seek(0)
                    file = discord.File(data)
                    return await ctx.send(file=file)
                else:
                    await ctx.send(f"API returned status code: {resp.status}")

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def aivase(self, ctx: commands.Context):
        """Responds with randomly AI generated vase (or vessel)."""
        async with ctx.typing():
            x = random.randint(0, 20000)
            x = str(x).zfill(7)
            link = f"http://thisvesseldoesnotexist.s3-website-us-west-2.amazonaws.com/public/v2/fakes/{x}.jpg"
            async with self.session.get(link) as resp:
                if resp.status == 200:
                    data = BytesIO(await resp.read())
                    data.name = "ai-vase.jpg"
                    data.seek(0)
                    file = discord.File(data)
                    return await ctx.send(file=file)
                else:
                    await ctx.send(f"API returned status code: {resp.status}")

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def aiwaifu(self, ctx: commands.Context):
        """Responds with randomly AI generated waifu."""
        async with ctx.typing():
            x = random.randint(0, 99999)
            link = f"https://www.thiswaifudoesnotexist.net/example-{x}.jpg"
            async with self.session.get(link) as resp:
                if resp.status == 200:
                    data = BytesIO(await resp.read())
                    data.name = "ai-waifu.jpg"
                    data.seek(0)
                    file = discord.File(data)
                    return await ctx.send(file=file)
                else:
                    await ctx.send(f"API returned status code: {resp.status}")
