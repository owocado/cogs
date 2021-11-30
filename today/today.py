import aiohttp
import asyncio
import calendar
from datetime import datetime, timezone
from random import choice

# Required by Red
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.menus import close_menu, menu, DEFAULT_CONTROLS


class Today(commands.Cog):
    """Various commands to show the stats about users' profile badges."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    __author__ = "ow0x (<@306810730055729152>)"
    __version__ = "0.1.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def today(self, ctx: commands.Context, day: int = None, month: int = None):
        """Get a random fact on what happened today in history.

        You can also fetch history facts for a specific day and month.
        """
        day = max(min(day, 31), 1) if day else datetime.now(timezone.utc).day
        month = max(min(month, 12), 1) if month else datetime.now(timezone.utc).month

        await ctx.trigger_typing()
        base_url = f"https://history.muffinlabs.com/date/{month}/{day}"
        try:
            async with self.session.get(base_url) as resp:
                if resp.status != 200:
                    return await ctx.send(f"https://http.cat/{resp.status}")
                data = await resp.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        pick_one = choice(data["data"]["Events"])
        year = pick_one.get("year", "Unknown year")
        text = pick_one.get("text", "No summary.")
        ext_links = [f"[{x.get('title')}]({x.get('link')})" for x in pick_one.get("links")]

        embed = discord.Embed(colour=await ctx.embed_color())
        embed.title = f"On this day ({data.get('date')}) ..."
        embed.url = data.get("url")
        embed.description = f"In **{year}** : {text}"
        if ext_links:
            embed.add_field(name="Related links", value="\n".join(ext_links))

        await ctx.send(embed=embed)

    @commands.command(aliases=["googledoodle"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def doodle(self, ctx: commands.Context, month: int = None, year: int = None):
        """Fetch Google doodle of the current day and month.

        Or doodles of specific month/year if `month` and `year` values are provided.
        """
        month = max(min(month, 12), 1) if month else datetime.now(timezone.utc).month
        year = year or datetime.now(timezone.utc).year

        await ctx.trigger_typing()
        base_url = f"https://www.google.com/doodles/json/{year}/{month}"
        try:
            async with self.session.get(base_url) as response:
                if response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                output = await response.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        if not output:
            return await ctx.send("Could not find any results.")

        pages = []
        for data in output:
            embed = discord.Embed(colour=await ctx.embed_color())
            embed.title = data.get("title", "Doodle title missing")
            img_url = data.get("high_res_url")
            if img_url and not img_url.startswith("https:"):
                img_url = "https:" + data.get("high_res_url")
            if not img_url:
                img_url = "https:" + data.get("url")
            embed.set_image(url=img_url)
            date = "-".join([str(x) for x in data.get("run_date_array")[::-1]])
            embed.set_footer(
                text=f"{data.get('share_text')}\nDoodle published on: {date}"
            )
            pages.append(embed)

        controls = {"❌": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=60.0)

    @commands.command()
    async def calendar(self, ctx: commands.Context, month: int = MONTH, year: int = YEAR):
        """Displays a calendar of current month or for a specific month for a specific year."""
        await ctx.send(box(calendar.month(year, month), lang="py"))
