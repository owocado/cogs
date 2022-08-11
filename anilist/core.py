import asyncio

import aiohttp
from redbot.core import commands
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .api.media import MediaData
from .embed_maker import generate_media_embed
from .schemas import MEDIA_SCHEMA


class Anilist(commands.Cog):
    """Fetch info on anime, manga, character, studio and more from Anilist!"""

    __authors__ = ["<@306810730055729152>"]
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
    async def anime(self, ctx: commands.Context, *, query: str):
        """Fetch info on any anime from given query!"""
        async with ctx.typing():
            results = await MediaData.request(
                self.session,
                query=MEDIA_SCHEMA,
                page=1,
                perPage=15,
                search=query,
                type="ANIME",
                sort="POPULARITY_DESC"
            )
            if type(results) is str:
                return await ctx.send(results)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = generate_media_embed(page)
                text = f"{emb.footer.text} • Page {i} of {len(results)}"
                emb.set_footer(text=text)
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command(aliases=["manhwa"])
    async def manga(self, ctx: commands.Context, *, query: str):
        """Fetch info on any manga from given query!"""
        async with ctx.typing():
            results = await MediaData.request(
                self.session,
                query=MEDIA_SCHEMA,
                page=1,
                perPage=15,
                search=query,
                type="MANGA",
                sort="POPULARITY_DESC"
            )
            if type(results) is str:
                return await ctx.send(results)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = generate_media_embed(page)
                text = f"{emb.footer.text} • Page {i} of {len(results)}"
                emb.set_footer(text=text)
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command()
    async def trending(self, ctx: commands.Context, media_type: str):
        """Fetch info on any manga from given query!"""
        if media_type.lower() not in ["anime", "manga"]:
            await ctx.send("Only `manga` or `anime` type is supported!")
            return

        async with ctx.typing():
            results = await MediaData.request(
                self.session,
                query=MEDIA_SCHEMA,
                page=1,
                perPage=15,
                type=media_type.upper(),
                sort="TRENDING_DESC"
            )
            if type(results) is str:
                return await ctx.send(results)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = generate_media_embed(page)
                text = f"{emb.footer.text} • Page {i} of {len(results)}"
                emb.set_footer(text=text)
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command()
    async def character(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch info on a anime/manga character from given query!"""
        ...

    @commands.command()
    async def studio(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch info on an animation studio from given query!"""
        ...
