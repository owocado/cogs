import asyncio

import aiohttp
from redbot.core import commands


class Anilist(commands.Cog):
    """Fetch info on anime, manga, character, studio and more from Anilist!"""

    __authors__ = "<@306810730055729152>"
    __version__ = "0.0.1"

    session = aiohttp.ClientSession()

    def cog_unload(self) -> None:
        asyncio.create_task(self.session.close())

    def format_help_for_context(self, ctx: commands.Context) -> str: # Thanks Sinbad!
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(self.__authors__)}\n"
            f"**Cog version:**  {self.__version__}"
        )

    async def cog_check(self, ctx: commands.Context) -> bool:
        if not ctx.guild:
            return True

        my_perms = ctx.channel.permissions_for(ctx.guild.me)
        return my_perms.embed_links and my_perms.send_messages

    @commands.command()
    async def anime(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch info on any anime from given query!"""
        ...

    @commands.command()
    async def manga(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch info on any manga from given query!"""
        ...

    @commands.command()
    async def character(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch info on a anime/manga character from given query!"""
        ...

    @commands.command()
    async def studio(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch info on an animation studio from given query!"""
        ...
