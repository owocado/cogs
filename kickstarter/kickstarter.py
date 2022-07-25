from __future__ import annotations

import asyncio

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .api import KickstarterProject, NotFound


class Kickstarter(commands.Cog):
    """Get various nerdy info on a Kickstarter project."""

    __authors__ = ["dragonfire535", "ow0x"]
    __version__ = "2.0.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(self.__authors__)}\n"
            f"**Cog version:**  v{self.__version__}"
        )

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    session = aiohttp.ClientSession()

    def cog_unload(self) -> None:
        if self.session:
            asyncio.create_task(self.session.close())

    @staticmethod
    def make_embed(data: KickstarterProject, footer: str) -> discord.Embed:
        embed = discord.Embed(colour=0x14E06E, title=data.name or "")
        if data.urls and data.urls.web:
            embed.url = data.urls.web.get('project', '') or ''
        embed.set_author(name="Kickstarter", icon_url="https://i.imgur.com/EHDlH5t.png")
        if data.photo:
            embed.set_image(url=data.photo.h864 or data.photo.full)
        embed.add_field(name="Project Goal", value=data.project_goal)
        embed.add_field(name="Pledged", value=data.pledged_till_now)
        embed.add_field(name="Backers", value=f'{humanize_number(data.backers_count)}')
        embed.description = (
            f"{data.blurb or ''}\n\n{data.who_created}\n"
            f"{data.when_created}{data.when_launched}{data.when_deadline}"
        )
        embed.set_footer(text=f"{footer} • Category: {data.category}")
        return embed

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def kickstarter(self, ctx: commands.Context, *, query: str):
        """Search for a project on Kickstarter by given query."""
        query = query.replace(" ", "%20").lower()
        url = f"https://www.kickstarter.com/projects/search.json?term={query}"

        async with ctx.typing():
            projects = await KickstarterProject.request(self.session, url)
            if isinstance(projects, NotFound):
                return await ctx.send(f"❌ No results! {projects}")

            pages = []
            for i, data in enumerate(projects, start=1):
                footer = f"Page {i} of {len(projects)}"
                embed = self.make_embed(data, footer)
                pages.append(embed)

        if len(pages) == 1:
            return await ctx.send(embed=pages[0])
        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=90.0)
