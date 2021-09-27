import aiohttp
import asyncio
import random

from io import BytesIO
from cairosvg import svg2png

import discord
from redbot.core import commands

SR_API_URL = "https://some-random-api.ml/premium/amongus"
PETPET_API = "https://some-random-api.ml/premium/petpet"
ALEX_API_URL = "https://api.alexflipnote.dev"


class ImageCog(commands.Cog):
    """Various fun image generation commands."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.0.5"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.dicebear_endpoints = [
            "male",
            "female",
            "initials",
            "identicon",
            "jdenticon",
            "bottts",
            "avataaars",
            "human",
        ]

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command(aliases=["amongus"])
    @commands.bot_has_permissions(attach_files=True)
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def eject(self, ctx: commands.Context, *, member: discord.Member = None):
        """Find out if someone is an imposter or not :kappa:

        ⚠ **NOTE: This command requires a free API key.**
        You can find out how to get one at:
        https://some-random-api.ml/docs/Welcome/Keys

        Once you have received your key, set it in your red instance with:
        `[p]set api srapi api_key <api_key>`
        """
        if not member:
            member = ctx.author

        api_key = (await ctx.bot.get_shared_api_tokens("srapi")).get("api_key")
        if not api_key:
            return await ctx.send_help()

        params = {
            "username": str(member.name),
            "avatar": str(member.avatar_url_as(format="png")),
            "impostor": random.choice(["true", "false"]),
            "key": api_key,
        }

        await ctx.trigger_typing()
        try:
            async with self.session.get(SR_API_URL, params=params) as resp:
                if 300 > resp.status >= 200:
                    fp = BytesIO(await resp.read())
                    await ctx.send(file=discord.File(fp, "amogus.gif"))
                    return
                else:
                    await ctx.send("Couldn't get image from API. :(")
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out.")

    @commands.command()
    @commands.bot_has_permissions(attach_files=True)
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def petpet(self, ctx: commands.Context, *, member: discord.Member = None):
        """Petpet someone in high quality.

        ⚠ **NOTE: This command requires a free API key.**
        You can find out how to get one at:
        https://some-random-api.ml/docs/Welcome/Keys

        Once you have received your key, set it in your red instance with:
        `[p]set api srapi api_key <api_key>`
        """
        if not member:
            member = ctx.author

        api_key = (await ctx.bot.get_shared_api_tokens("srapi")).get("api_key")
        if not api_key:
            return await ctx.send_help()

        params = {"avatar": str(member.avatar_url_as(format="png")), "key": api_key}

        await ctx.trigger_typing()
        try:
            async with self.session.get(PETPET_API, params=params) as resp:
                if 300 > resp.status >= 200:
                    fp = BytesIO(await resp.read())
                    await ctx.send(file=discord.File(fp, "petpet.gif"))
                    return
                else:
                    await ctx.send("Couldn't get image from API. :(")
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out.")

    @commands.command()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def dicebear(
        self, ctx: commands.Context, text: str = None, avatar_type: str = "avataaars"
    ):
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
        await ctx.trigger_typing()
        try:
            async with self.session.get(base_url) as response:
                if response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                avatar = await response.read()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        attachment = BytesIO(svg2png(bytestring=avatar))
        await ctx.send(file=discord.File(attachment, "dicebear.png"))

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def shields(
        self,
        ctx: commands.Context,
        subject: str,
        status: str,
        color: str = "brightgreen",
    ):
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
            return await ctx.send(
                "Supported values for `roboset` parameter are: `set1`, `set2`, `set3`, `set4`."
            )

        await ctx.send(f"https://robohash.org/{text}.png?set={roboset}")

    @commands.command()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def pornhub(self, ctx: commands.Context, text1: str, text2: str):
        """Generate a PornHub style logo from 2 given words through alexflipnote API.

        ⚠ **NOTE: This command requires a free API key.**

        You can request for one in AlexFlipnote discord server:
        https://discord.gg/DpxkY3x (in their #support channel)
        Once you have received your key, set it in your red instance with:
        `[p]set api alexflipnote api_key <api_key>`
        """
        api_key = (await ctx.bot.get_shared_api_tokens("alexflipnote")).get("api_key")
        if not api_key:
            return await ctx.send_help()

        headers = {"Authorization": api_key}
        await ctx.trigger_typing()
        try:
            async with self.session.get(
                ALEX_API_URL + f"/pornhub?text={text1}&text2={text2}", headers=headers
            ) as response:
                if response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                fp = BytesIO(await response.read())
                fp.seek(0)
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out.")
            return

        await ctx.send(file=discord.File(fp, "pornhub.png"))

    @commands.command(aliases=["aiart"])
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def aiartwork(self, ctx: commands.Context):
        """Responds with randomly AI generated artwork."""
        await ctx.trigger_typing()
        try:
            async with self.session.get("https://thisartworkdoesnotexist.com/") as resp:
                if resp.status != 200:
                    return await ctx.send(f"API returned status code: {resp.status}")
                data = BytesIO(await resp.read())
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        data.name = "ai-artwork.jpg"
        data.seek(0)
        file = discord.File(data)
        await ctx.send(file=file)

    @commands.command(aliases=["aikitty"])
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def aicat(self, ctx: commands.Context):
        """Responds with randomly AI generated cat."""
        await ctx.trigger_typing()
        try:
            async with self.session.get("https://thiscatdoesnotexist.com/") as resp:
                if resp.status != 200:
                    return await ctx.send(f"API returned status code: {resp.status}")
                data = BytesIO(await resp.read())
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        data.name = "ai-kitty.jpg"
        data.seek(0)
        file = discord.File(data)
        await ctx.send(file=file)

    @commands.command(aliases=["aifurry"])
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def aifursona(self, ctx: commands.Context):
        """Responds with randomly AI generated furry persona."""
        await ctx.trigger_typing()
        rint = random.randint(0, 99999)
        base_url = f"http://thisfursonadoesnotexist.com/v2/jpgs/seed{rint}.jpg"
        try:
            async with self.session.get(base_url) as resp:
                if resp.status != 200:
                    return await ctx.send(f"API returned status code: {resp.status}")
                data = BytesIO(await resp.read())
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        data.name = "ai-fursona.jpg"
        data.seek(0)
        file = discord.File(data)
        await ctx.send(file=file)

    @commands.command()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def aihorse(self, ctx: commands.Context):
        """Responds with randomly AI generated horse."""
        await ctx.trigger_typing()
        try:
            async with self.session.get("https://thishorsedoesnotexist.com/") as resp:
                if resp.status != 200:
                    return await ctx.send(f"API returned status code: {resp.status}")
                data = BytesIO(await resp.read())
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        data.name = "ai-horse.jpg"
        data.seek(0)
        file = discord.File(data)
        await ctx.send(file=file)

    @commands.command()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def aiperson(self, ctx: commands.Context):
        """Responds with randomly AI generated human face."""
        await ctx.trigger_typing()
        try:
            async with self.session.get(
                "https://thispersondoesnotexist.com/image"
            ) as resp:
                if resp.status != 200:
                    return await ctx.send(f"API returned status code: {resp.status}")
                data = BytesIO(await resp.read())
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        data.name = "ai-person.jpg"
        data.seek(0)
        file = discord.File(data)
        await ctx.send(file=file)

    @commands.command()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def aivase(self, ctx: commands.Context):
        """Responds with randomly AI generated vase (or vessel)."""
        await ctx.trigger_typing()
        x = random.randint(0, 20000)
        x = str(x).zfill(7)
        base_url = f"http://thisvesseldoesnotexist.s3-website-us-west-2.amazonaws.com/public/v2/fakes/{x}.jpg"
        try:
            async with self.session.get(base_url) as resp:
                if resp.status != 200:
                    return await ctx.send(f"API returned status code: {resp.status}")
                data = BytesIO(await resp.read())
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        data.name = "ai-vase.jpg"
        data.seek(0)
        file = discord.File(data)
        await ctx.send(file=file)

    @commands.command()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def aiwaifu(self, ctx: commands.Context):
        """Responds with randomly AI generated waifu."""
        await ctx.trigger_typing()
        x = random.randint(0, 99999)
        base_url = f"https://www.thiswaifudoesnotexist.net/example-{x}.jpg"
        try:
            async with self.session.get(base_url) as resp:
                if resp.status != 200:
                    return await ctx.send(f"API returned status code: {resp.status}")
                data = BytesIO(await resp.read())
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        data.name = "ai-waifu.jpg"
        data.seek(0)
        file = discord.File(data)
        await ctx.send(file=file)

    @commands.command(name="picsum")
    @commands.bot_has_permissions(embed_links=True)
    async def lorem_picsum(self, ctx: commands.Context, width: int = None, height: int = None):
        """Fetch a random dummy or placeholder image of certain width X height.

        Maximum supported size for `width` and `height` args is 2000 px, and minimum is 10 px.
        """
        width = width if width else 600
        height = height if height else 600
        width = 600 if (width > 2000 or width < 10) else width
        height = 600 if (height > 2000 or height < 10) else height

        await ctx.trigger_typing()
        try:
            async with self.session.get(f"https://picsum.photos/{width}/{height}") as resp:
                if resp.status != 200:
                    return await ctx.send(f"https://http.cat/{resp.status}")
                image = BytesIO(await resp.read())
                image.seek(0)
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        await ctx.send(file=discord.File(image, "picsum.jpg"))
