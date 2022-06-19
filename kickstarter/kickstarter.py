import asyncio
from datetime import datetime, timezone

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number as hnum
from redbot.core.utils.menus import close_menu, menu, DEFAULT_CONTROLS


class Kickstarter(commands.Cog):
    """Get various nerdy info on a Kickstarter project."""

    __authors__ = ["ow0x"]
    __version__ = "1.0.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"Authors:  {', '.join(self.__authors__)}\n"
            f"Cog version:  v{self.__version__}"
        )

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    @staticmethod
    async def get(ctx, base_url: str):
        try:
            async with aiohttp.request("GET", base_url) as response:
                if response.status != 200:
                    await ctx.send(f"https://http.cat/{response.status}")
                    return None
                return await response.json()
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out.")
            return None

    @staticmethod
    def make_embed(data, footer: str):
        embed = discord.Embed(colour=0x14E06E, title=data.get("name", ""))
        if data.get("urls", {}).get("web"):
            embed.url = data.get("urls").get("web").get("project")
        embed.set_author(name="Kickstarter", icon_url="https://i.imgur.com/EHDlH5t.png")
        project_summary = data.get("blurb", "No summary.")
        if data.get("photo"):
            embed.set_image(url=data["photo"].get("full", ""))
        embed.add_field(
            name="Goal", value=f"{data.get('currency_symbol')}{hnum(round(data.get('goal', 0)))}",
        )
        pledged = f"{data.get('currency_symbol')}{hnum(round(data.get('pledged')))}"
        percent_funded = round((data.get('pledged') / data.get('goal')) * 100)
        pretty_pledged = f"{pledged}\n({hnum(percent_funded)}% funded)"
        embed.add_field(name="Pledged", value=pretty_pledged)
        embed.add_field(name="Backers", value=hnum(data.get("backers_count", 0)))
        creator = f"[{data.get('creator').get('name')}]({data['creator']['urls']['web']['user']})"
        deadline = datetime.utcfromtimestamp(data.get("deadline"))
        past_or_future = "`**EXPIRED**`" if datetime.now(timezone.utc).replace(tzinfo=None) > deadline else ""
        embed.description = (
            f"{project_summary}\n\n**Creator**: {creator}\n"
            f"**Creation Date**: <t:{int(data.get('created_at'))}:R>\n"
            f"**Launched Date**: <t:{int(data.get('launched_at'))}:R>\n"
            f"**Deadline**: <t:{int(data.get('deadline'))}:R> {past_or_future}\n"
        )
        if data.get("category"):
            footer += f" | Category: {data.get('category').get('name')}"
        embed.set_footer(text=footer)
        return embed

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def kickstarter(self, ctx: commands.Context, *, query: str):
        """Search for a project on Kickstarter."""
        base_url = f"https://www.kickstarter.com/projects/search.json?term={query}"

        async with ctx.typing():
            data = await self.get(ctx, base_url)
            if data is None: return
            if len(data["projects"]) == 0 and data["total_hits"] == 0:
                return await ctx.send(f"\u26d4 No results. Did you mean `{data['suggestion']}`?")

            pages = []
            for i, result in enumerate(data["projects"], start=1):
                footer = f"Page {i} of {len(data['projects'])}"
                embed = self.make_embed(result, footer)
                pages.append(embed)

        controls = {"❌": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=90.0)
