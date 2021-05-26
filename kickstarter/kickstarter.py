import aiohttp
import asyncio
import datetime

from dateutil import relativedelta

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS


class Kickstarter(commands.Cog):
    """Search for and get various info on a Kickstarter project."""

    __author__ = ["siu3334", "dragonfire535"]
    __version__ = "0.0.2"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3.0, commands.BucketType.member)
    async def kickstarter(self, ctx: commands.Context, *, query: str):
        """Search for a project on Kickstarter."""
        base_url = f"https://www.kickstarter.com/projects/search.json?term={query}"

        await ctx.trigger_typing()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    data = await response.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        if len(data["projects"]) == 0 and data["total_hits"] == 0:
            return await ctx.send(f"Could not find any results. Did you mean `{data['suggestion']}`?")

        pages = []
        for i, result in enumerate(data["projects"]):
            embed = discord.Embed(colour=0x14E06E)
            embed.title = result.get("name")
            embed.url = result.get("urls").get("web").get("project")
            embed.set_author(name="Kickstarter", icon_url="https://i.imgur.com/EHDlH5t.png")
            project_summary = result.get("blurb", "No summary.")
            if result.get("photo"):
                embed.set_thumbnail(url=result.get("photo").get("full"))
            embed.add_field(
                name="Goal",
                value=f"{result.get('currency_symbol')}{humanize_number(round(result.get('goal')))}",
            )
            pledged = f"{result.get('currency_symbol')}{humanize_number(round(result.get('pledged')))}"
            percent_funded = round((result.get('pledged') / result.get('goal')) * 100)
            pretty_pledged = f"{pledged}\n({humanize_number(percent_funded)}% funded)"
            embed.add_field(name="Pledged", value=pretty_pledged)
            embed.add_field(name="Backers", value=humanize_number(result.get("backers_count")))
            creator = f"[{result.get('creator').get('name')}]({result['creator']['urls']['web']['user']})"
            # embed.add_field(name="Creator", value=creator)
            created_at = datetime.datetime.utcfromtimestamp(result.get("created_at"))
            pretty_created = (
                created_at.strftime("%d %b, %Y") + f"\n({self._accurate_timedelta(created_at)} ago)"
            )
            # embed.add_field(name="Creation Date", value=pretty_created)
            launched_at = datetime.datetime.utcfromtimestamp(result.get("launched_at"))
            pretty_launched = (
                launched_at.strftime("%d %b, %Y") + f"\n({self._accurate_timedelta(launched_at)} ago)"
            )
            # embed.add_field(name="Launched Date", value=pretty_launched)
            deadline = datetime.datetime.utcfromtimestamp(result.get("deadline"))
            utcnow = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            past_or_future = "ago `**EXPIRED**`" if utcnow > deadline else "to go"
            pretty_deadline = (
                deadline.strftime("%d %b, %Y")
                + f"\n({self._accurate_timedelta(deadline)} {past_or_future})"
            )
            embed.description = (
                project_summary
                + f"**Creator**: {creator}\n"
                + f"**Creation Date**: {pretty_created}\n"
                + f"**Launched Date**: {pretty_launched}\n"
                + f"**Deadline**: {pretty_deadline}\n"
            )
            # embed.add_field(name="Deadline", value=pretty_deadline)
            footer = f"Page {i + 1} of {len(data['projects'])}"
            if result.get("category"):
                footer += f" | Category: {result.get('category').get('name')}"
            embed.set_footer(text=footer)
            pages.append(embed)

        if len(pages) == 1:
            return await ctx.send(embed=pages[0])
        else:
            await menu(ctx, pages, DEFAULT_CONTROLS, timeout=60.0)

    @staticmethod
    def _accurate_timedelta(date_time):
        dt1 = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        dt2 = date_time

        if dt1 > dt2:
            diff = relativedelta.relativedelta(dt1, dt2)
        else:
            diff = relativedelta.relativedelta(dt2, dt1)

        yrs, mths, days = (diff.years, diff.months, diff.days)
        hrs, mins, secs = (diff.hours, diff.minutes, diff.seconds)

        pretty = f"{yrs}y {mths}mth {days}d {hrs}h {mins}m {secs}s"
        to_join = " ".join([x for x in pretty.split() if x[0] != "0"][:2])

        return to_join
