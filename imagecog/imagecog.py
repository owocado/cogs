import aiohttp
import asyncio
import io
import random

import discord
from redbot.core import commands

SR_API_URL = "https://some-random-api.ml/premium/amongus"
PETPET_API = "https://some-random-api.ml/premium/petpet"


# Taken from https://github.com/flaree/Flare-Cogs/blob/master/dankmemer/dankmemer.py#L16
# Many thanks to flare <3
async def tokencheck(ctx):
    token = await ctx.bot.get_shared_api_tokens("srapi")
    return bool(token.get("api_key"))


class ImageCog(commands.Cog):
    """Various fun image generation commands."""

    __author__ = "<@306810730055729152>"
    __version__ = "0.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command(aliases=["amongus"])
    @commands.check(tokencheck)
    @commands.bot_has_permissions(attach_files=True)
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def eject(self, ctx: commands.Context, *, member: discord.Member = None):
        """Find out if someone is an imposter or not :kappa:"""
        if not member:
            member = ctx.author

        service = await ctx.bot.get_shared_api_tokens("srapi")
        api_key = service.get("api_key")

        params = {
            "username": str(member.name),
            "avatar": str(member.avatar_url_as(format="png")),
            "impostor": random.choice(['true', 'false']),
            "key": api_key
        }

        async with ctx.typing():
            try:
                async with self.session.get(SR_API_URL, params=params) as resp:
                    if 300 > resp.status >= 200:
                        fp = io.BytesIO(await resp.read())
                        await ctx.send(file=discord.File(fp, "amogus.gif"))
                        return
                    else:
                        await ctx.send("Couldn't get image from API. :(")
            except asyncio.TimeoutError:
                await ctx.send("Operation timed out.")

    @commands.command()
    @commands.check(tokencheck)
    @commands.bot_has_permissions(attach_files=True)
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def petpet(self, ctx: commands.Context, *, member: discord.Member = None):
        """Petpet someone in high quality."""
        if not member:
            member = ctx.author

        service = await ctx.bot.get_shared_api_tokens("srapi")
        api_key = service.get("api_key")

        params = {
            "avatar": str(member.avatar_url_as(format='png')),
            "key": api_key
        }

        async with ctx.typing():
            try:
                async with self.session.get(PETPET_API, params=params) as resp:
                    if 300 > resp.status >= 200:
                        fp = io.BytesIO(await resp.read())
                        await ctx.send(file=discord.File(fp, "petpet.gif"))
                        return
                    else:
                        await ctx.send("Couldn't get image from API. :(")
            except asyncio.TimeoutError:
                await ctx.send("Operation timed out.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def dicebear(self, ctx: commands.Context, gender: str, emotion: str, *, name: str):
        """Fetch a random avatar from Dicebear API"""
        if gender not in ["male", "female"]:
            return await ctx.send("Only `male` or `female` gender is allowed for gender parameter.")

        if emotion not in ["happy", "sad", "surprised"]:
            return await ctx.send("Valid values for emotion parameter are either `happy`, `sad` or `surprised`.")

        await ctx.send(f"https://avatars.dicebear.com/api/{gender}/{name}.png?width=285&height=285&mood[]={emotion}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def adorable(self, ctx: commands.Context, text: str):
        """Fetch an \"adorable\" avatar."""

        await ctx.send(f"https://api.hello-avatar.com/adorables/285/{text}.png")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def shields(self, ctx: commands.Context, subject: str, status: str, color: str = "brightgreen"):
        """Fetch a shields.io badge"""

        subject = subject.replace("-", "--").replace("_", "__")
        status = status.replace("-", "--").replace("_", "__")

        await ctx.send(f"https://img.shields.io/badge/{subject}-{status}-{color}.png")
