import aiohttp
import asyncio
import io
import random

from cairosvg import svg2png

import discord
from redbot.core import commands

SR_API_URL = "https://some-random-api.ml/premium/amongus"
PETPET_API = "https://some-random-api.ml/premium/petpet"
ALEX_API_URL = "https://api.alexflipnote.dev"


# Taken from https://github.com/flaree/Flare-Cogs/blob/master/dankmemer/dankmemer.py#L16
# Many thanks to flare <3
async def tokencheck(ctx):
    token = await ctx.bot.get_shared_api_tokens("srapi")
    return bool(token.get("api_key"))


class ImageCog(commands.Cog):
    """Various fun image generation commands."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.0.2"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.dicebear_endpoints = ["male", "female", "initials", "identicon", "jdenticon", "bottts", "avataaars", "human"]

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
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def dicebear(self, ctx: commands.Context, text: str = Non, avatar_type: str = "avataaars"):
        """Fetch a random avatar from Dicebear API.

        Following Dicebear avatar types are supported:
        `male`, `female`, `initials`, `identicon`, `jdenticon`, `bottts`, `avataaars`, `human`

        Try them out to see what kind of avatar each endpoint returns.
        Probably something funny or amusing or something meh.
        """
        if avatar_type not in self.dicebear_endpoints:
            return await ctx.send(
                f"Supported avatar types are: {', '.join(self.dicebear_endpoints)}"
            )
        text = str(ctx.author.name) if not text else text
        base_url = f"https://avatars.dicebear.com/api/{avatar_type}/{text}.svg?width=600&height=600"
        async with ctx.typing():
            try:
                async with self.session.get(base_url) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    avatar = await response.read()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            attachment = io.BytesIO(svg2png(bytestring=avatar))
            await ctx.send(file=discord.File(attachment, "dicebear.png"))

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def adorable(self, ctx: commands.Context, text: str):
        """Fetch an \"adorable\" avatar."""

        await ctx.send(f"https://api.hello-avatar.com/adorables/400/{text}.png")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def shields(self, ctx: commands.Context, subject: str, status: str, color: str = "brightgreen"):
        """Fetch a shields.io badge"""

        subject = subject.replace("-", "--").replace("_", "__")
        status = status.replace("-", "--").replace("_", "__")

        await ctx.send(f"https://img.shields.io/badge/{subject}-{status}-{color}.png")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def robohash(self, ctx: commands.Context, text: str, roboset: str = "set1"):
        """Fetch a unique, robot/alien/monster/kittens avatar for any given text.

        Optionally, there are 4 sets you can pass with `roboset` arg. Defaults to set1.
        `set2` -  generates a whole slew of Random monster looking avatars.
        `set3` -  generates avatar resembling robots. New, suave, disembodied heads.
        `set4` -  hydroponically grow avatar of beautiful kittens.
        """
        if roboset not in ["set1", "set2", "set3", "set4"]:
            return await ctx.send("Only supported values for `roboset` parameter are `set1`, `set2`, `set3`, `set4`.")

        await ctx.send(f"https://robohash.org/{text}.png?set={roboset}")

    @commands.command()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def pornhub(self, ctx: commands.Context, text1: str, text2: str):
        """Generate a PornHub style logo from 2 given words through alexflipnote API.

        ⚠ **NOTE: This command requires an API key.**

        You can request for one in AlexFlipnote discord server:
        https://discord.gg/DpxkY3x (in their #support channel)
        Once you have received your key, set it in your red instance with:
        `[p]set api alexflipnote api_key <api_key>`
        """
        api_key = (await ctx.bot.get_shared_api_tokens("alexflipnote")).get("api_key")
        if api_key is None:
            return await ctx.send_help()

        headers = {"Authorization": api_key}
        async with ctx.typing():
            try:
                async with self.session.get(
                    ALEX_API_URL + f"/pornhub?text={text1}&text2={text2}",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    fp = io.BytesIO(await response.read())
                    fp.seek(0)
            except asyncio.TimeoutError:
                await ctx.send("Operation timed out.")
                return

            await ctx.send(file=discord.File(fp, "pornhub.png"))
