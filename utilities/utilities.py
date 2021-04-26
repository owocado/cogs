import aiohttp
import asyncio
import datetime

from dateutil import relativedelta
from io import BytesIO

import discord
from redbot.core import commands


class Utilities(commands.Cog):
    """Some of my useful utility commands."""

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

    @commands.command()
    async def snowflake(self, ctx: commands.Context, snowflake: int, snowflake2: int = None):
        """Convert a snowflake to human relative datetime timedelta

        or compare timedelta difference between 2 snowflakes.
        """
        try:
            snowflake = discord.utils.snowflake_time(snowflake)
        except (ValueError, OverflowError):
            await ctx.send("Value of given `snowflake` parameter is out of range.")
            return
        if snowflake2 is None:
            snowflake2 = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        else:
            try:
                snowflake2 = discord.utils.snowflake_time(snowflake2)
            except (ValueError, OverflowError):
                await ctx.send("Value of given `snowflake2` parameter is out of range.")
                return

        diff = self._accurate_timedelta(snowflake, snowflake2)
        strftime1 = snowflake.strftime("%A, %d %B, %Y at %H:%M:%S")
        strftime2 = "Time 2: " + snowflake2.strftime("%A, %d %B, %Y at %H:%M:%S") if snowflake2 else ""

        final_message = (
            f"Time : {strftime1} UTC\n{strftime2}\n"
            f"Difference: {diff}"
        )

        await ctx.send(final_message)

    @commands.command()
    async def inviscount(self, ctx: commands.Context, *, role: discord.role):
        """Get number (and %) of offline users in a given role."""
        if role is None:
            return await ctx.send("Please provide a valid role name or role ID.")

        users = [a for a in ctx.guild.members if role in a.roles]
        count = len([m for m in ctx.guild.members if role in m.roles])
        if count == 0:
            return await ctx.send(f"No one has `{role.name}` role yet. 🤔")
        offline = sum(x.status == discord.Status.offline for x in users)
        percent = offline / count

        to_send = f"({round(percent * 100, 2)}%) __**{offline}**__ out of {count} users in **{role.name}** role are currently offline."
        await ctx.send(to_send)

    @commands.command(aliases=["urlshorten"])
    async def bitly(self, ctx: commands.Context, url: str, custom_bitlink: str = None):
        """Generate a shortened URL with Bitly API.

        This command requires a generic access token from Bitly.
        You can get one free from: https://bitly.is/accesstoken
        You will be require to register for an account first.

        Once you have the token, set it with:
        ```
        [p]set api bitly api_key <access_token>
        ```
        """
        api_key = (await ctx.bot.get_shared_api_tokens("bitly")).get("api_key")
        if api_key is None:
            return await ctx.send_help()

        head = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
        payload = {"long_url": url, "domain": "bit.ly"}
        base_url = "https://api-ssl.bitly.com/v4/shorten"
        async with ctx.typing():
            try:
                async with self.session.post(base_url, headers=head, json=payload) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    data = await response.json()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            link = data.get("link", "Missing shortened URL.")

            if custom_bitlink is None:
                return await ctx.send(link)

            bitlink_id = data.get("id", "bitly.is ID missing.").replace("bitly.is", "bit.ly")
            xpayload = {"custom_bitlink": custom_bitlink, "bitlink_id": bitlink_id}
            xbase_url = "https://api-ssl.bitly.com/v4/custom_bitlinks"
            try:
                async with self.session.post(xbase_url, headers=head, json=xpayload) as resp:
                    if resp.status != 200:
                        return await ctx.send(f"https://http.cat/{resp.status}")
                    output = await resp.json()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            custom_link = output.get("bitlink").get("custom_bitlinks")[0]
            await ctx.send(custom_link)

    @commands.command()
    @commands.is_owner()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def thumio(self, ctx: commands.Context, url: str):
        """Get a free landspace screenshot of a valid publicly accessible webpage."""
        base_url = f"https://image.thum.io/get/width/1920/crop/675/noanimate/{url}"
        async with ctx.typing():
            try:
                async with self.session.get(base_url) as resp:
                    if resp.status != 200:
                        return await ctx.send(f"https://http.cat/{resp.status}")
                    data = BytesIO(await resp.read())
                    data.seek(0)
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            await ctx.send(file=discord.File(data, "screenshot.png"))

    @commands.command()
    @commands.is_owner()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def screenshot(
        self,
        ctx: commands.Context,
        web_url: str,
        width: int = 1680,
        height: int = 876,
        full_page: str = "false",
        fresh: str = "true",
        block_ads: str = "false",
        no_cookie_banners: str = "false",
        omit_background: str = "false",
        dark_mode: str = "false",
        lazy_load: str = "false",
        destroy_screenshot: str = "true",
    ):
        """Get a screenshot of a valid publicly accessible webpage.

        This command requires an API token. You can get a free token
        by registering a free account on https://screenshotapi.net

        Once you have the API token, set it with:
        ```
        [p]set api screenshotapi api_key <api_token>
        ```
        Please note: free API token quota is limited to 100 screenshots per month.
        """
        api_key = (await ctx.bot.get_shared_api_tokens("screenshotapi")).get("api_key")
        if api_key is None:
            return await ctx.send_help()

        width = 1920 if width > 7680 else width
        height = 1080 if height > 4320 else height
        full_page = "false" if full_page not in ["true", "false"] else full_page
        fresh = "true" if fresh not in ["true", "false"] else fresh
        block_ads = "false" if block_ads not in ["true", "false"] else block_ads
        no_cookie_banners = "false" if no_cookie_banners not in ["true", "false"] else no_cookie_banners
        omit_background = "false" if omit_background not in ["true", "false"] else omit_background
        dark_mode = "false" if dark_mode not in ["true", "false"] else dark_mode
        lazy_load = "false" if lazy_load not in ["true", "false"] else lazy_load
        destroy_screenshot = "true" if destroy_screenshot not in ["true", "false"] else destroy_screenshot

        base_url = "https://shot.screenshotapi.net/screenshot"
        params = {
            "token": api_key,
            "url": web_url,
            "width": width,
            "height": height,
            "full_page": full_page,
            "fresh": fresh,
            "output": "image",
            "file_type": "png",
            "block_ads": block_ads,
            "no_cookie_banners": no_cookie_banners,
            "destroy_screenshot": destroy_screenshot,
            "dark_mode": dark_mode
        }

        async with ctx.typing():
            try:
                async with self.session(base_url, params=params) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    data = BytesIO(await response.read())
                    data.seek(0)
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            await ctx.send(file=discord.File(data, "screenshot.png"))

    @staticmethod
    def _accurate_timedelta(value1, value2):
        if value1 > value2:
            diff = relativedelta.relativedelta(value1, value2)
        else:
            diff = relativedelta.relativedelta(value2, value1)

        yrs, mths, days = (diff.years, diff.months, diff.days)
        hrs, mins, secs = (diff.hours, diff.minutes, diff.seconds)

        pretty = f"{yrs}y {mths}mth {days}d {hrs}h {mins}m {secs}s"
        to_join = " ".join([x for x in pretty.split() if x[0] != '0'][:3])

        return to_join
