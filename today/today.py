import aiohttp
import asyncio
import calendar
import datetime

from random import choice

# Required by Red
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS


class Today(commands.Cog):
    """Various commands to show the stats about users' profile badges."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.1.0"

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
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def today(self, ctx: commands.Context, day: int = None, month: int = None):
        """Responds with random fact on what happened today in history.

        You can also search for a random history event for a specific DD-MM (day and month)
        """
        day = (
            datetime.datetime.now(datetime.timezone.utc).day
            if (day > 31 or day < 1 or not day)
            else day
        )
        month = (
            datetime.datetime.now(datetime.timezone.utc).month
            if (month > 12 or month < 1 or not month)
            else month
        )
        base_url = f"https://history.muffinlabs.com/date/{month}/{day}"
        async with ctx.typing():
            try:
                async with self.session.get(base_url) as resp:
                    if resp.status != 200:
                        return await ctx.send(f"https://http.cat/{resp.status}")
                    data = await resp.json()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            pick = choice(data["data"]["Events"])
            year = pick.get("year", "Unknwon year")
            text = pick.get("text", "No summary.")
            related_links = ""
            for link in pick.get("links"):
                related_links += "[{}]({})\n".format(
                    link.get("title"), link.get("link")
                )

            embed = discord.Embed(colour=await ctx.embed_color())
            embed.title = f"On this day ({data.get('date', 'Unknown date')}) ..."
            embed.url = data.get("url")
            embed.description = f"In {year} : {text}"
            embed.add_field(name="Related links", value=related_links, inline=False)
            await ctx.send(embed=embed)

    @commands.command(aliases=["doodle"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def googledoodle(
        self, ctx: commands.Context, month: int = None, year: int = None
    ):
        """Responds with Google doodles of the current day and month.

        Or doodles of specific month/year if `month` and `year` values are provided.
        """
        month = (
            datetime.datetime.now(datetime.timezone.utc).month
            if (month > 12 or month < 1 or not month)
            else month
        )
        year = datetime.datetime.now(datetime.timezone.utc).year if not year else year

        async with ctx.typing():
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

        if len(pages) == 1:
            return await ctx.send(embed=pages[0])
        else:
            await menu(ctx, pages, DEFAULT_CONTROLS, timeout=60.0)

    @commands.command()
    async def calendar(self, ctx: commands.Context, month: int = None, year: int = None):
        """Displays a calendar of current month or for a specific month for a specific year."""
        month = (
            datetime.datetime.now(datetime.timezone.utc).month
            if (month > 12 or month < 1 or not month)
            else month
        )

        await ctx.send(box(calendar.month(year, month), lang="py"))
