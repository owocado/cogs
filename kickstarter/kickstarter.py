import asyncio
from datetime import datetime, timezone

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.menus import close_menu, menu, DEFAULT_CONTROLS


class Kickstarter(commands.Cog):
    """Get various nerdy info on a Kickstarter project."""

    __authors__ = "ow0x, dragonfire535"
    __version__ = "0.1.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {self.__authors__}\nCog Version: {self.__version__}"
    
    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3.0, commands.BucketType.member)
    async def kickstarter(self, ctx: commands.Context, *, query: str):
        """Search for a project on Kickstarter."""
        base_url = f"https://www.kickstarter.com/projects/search.json?term={query}"

        await ctx.trigger_typing()
        try:
            async with aiohttp.request("GET", base_url) as response:
                if response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                data = await response.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        if len(data["projects"]) == 0 and data["total_hits"] == 0:
            return await ctx.send(f"Could not find any results. Did you mean `{data['suggestion']}`?")

        pages = []
        for i, result in enumerate(data["projects"], start=1):
            embed = discord.Embed(colour=0x14E06E)
            embed.title = result.get("name")
            if result.get("urls", {}).get("web"):
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
            deadline = datetime.datetime.utcfromtimestamp(result.get("deadline"))
            past_or_future = "`**EXPIRED**`" if datetime.now(timezone.utc).replace(tzinfo=None) > deadline else ""
            embed.description = (
                project_summary
                + f"\n\n**Creator**: {creator}\n"
                f"**Creation Date**: <t:{int(result.get('created_at'))}:R>\n"
                f"**Launched Date**: <t:{int(result.get('launched_at'))}:R>\n"
                f"**Deadline**: <t:{int(result.get('deadline'))}:R> {past_or_future}\n"
            )
            footer = f"Page {i} of {len(data['projects'])}"
            if result.get("category"):
                footer += f" | Category: {result.get('category').get('name')}"
            embed.set_footer(text=footer)
            pages.append(embed)

        controls = {"❌": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=90.0)
