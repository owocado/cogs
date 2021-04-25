import aiohttp
import asyncio

from datetime import datetime

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS


class Kickstarter(commands.Cog):
    """Search for your query to fetch info on a Kickstarter project."""

    __author__ = ["siu3334 (<@306810730055729152>)", "dragonfire535"]
    __version__ = "0.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def kickstarter(self, ctx: commands.Context, *, query: str):
        """Search for a project on Kickstarter."""
        base_url = "https://www.kickstarter.com/projects/search.json"
        params = {"term": query}
        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(base_url, params=params) as response:
                        if response.status != 200:
                            return await ctx.send(f"https://http.cat/{response.status}")
                        data = await response.json()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            if len(data.get("projects")) == 0:
                return await ctx.send("Could not find any result.")

            embed_list = []
            for result in data.get("projects"):
                em = discord.Embed(colour=0x14E06E)
                em.title = result.get("name")
                em.url = result.get("urls").get("web").get("project")
                em.set_author(name="Kickstarter", icon_url="https://i.imgur.com/EHDlH5t.png")
                em.description = result.get("blurb", "No summary.")
                if result.get("photo"):
                    em.set_thumbnail(url=result.get("photo").get("full"))
                em.add_field(name="Goal", value=f"{result.get('currency_symbol')}{humanize_number(round(result.get('goal')))}")
                em.add_field(name="Pledged", value=f"{result.get('currency_symbol')}{humanize_number(round(result.get('pledged')))}")
                em.add_field(name="Backers", value=humanize_number(result.get("backers_count")))
                creator = f"[{result.get('creator').get('name')}]({result.get('creator').get('urls').get('web').get('user')})"
                em.add_field(name="Creator", value=creator)
                created_at = datetime.utcfromtimestamp(result.get("created_at")).strftime("%d %b, %Y")
                em.add_field(name="Creation Date", value=created_at)
                deadline = datetime.utcfromtimestamp(result.get("deadline")).strftime("%d %b, %Y")
                em.add_field(name="Deadline", value=deadline)
                if result.get("category"):
                    em.set_footer(text=f"Category: {result.get('category').get('name')}")
                embed_list.append(em)

        if not embed_list:
            return await ctx.send("No results.")
        elif len(embed_list) == 1:
            return await ctx.send(embed=embed_list[0])
        else:
            await menu(ctx, embed_list, DEFAULT_CONTROLS, timeout=60.0)
