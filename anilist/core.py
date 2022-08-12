import asyncio

import aiohttp
from redbot.core import commands
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .api.character import CharacterData
from .api.media import MediaData
from .embed_maker import generate_character_embed, generate_media_embed
from .schemas import (
    CHARACTER_SCHEMA,
    GENRE_SCHEMA,
    MEDIA_SCHEMA,
    TAG_SCHEMA
)


class Anilist(commands.Cog):
    """Fetch info on anime, manga, character, studio and more from Anilist!"""

    __authors__ = ["<@306810730055729152>"]
    __version__ = "0.0.6"

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
                emb = generate_media_embed(page, ctx.channel.is_nsfw())
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
                emb = generate_media_embed(page, ctx.channel.is_nsfw())
                emb.set_footer(text=f"{emb.footer.text} • Page {i} of {len(results)}")
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command()
    # TODO: use typing.Literal for media_type with dpy 2.x
    async def trending(self, ctx: commands.Context, media_type: str):
        """Fetch currently trending animes or manga from AniList!"""
        if media_type.lower() not in ["anime", "manga"]:
            return await ctx.send(
                "You provided invalid media type! Only `manga` or `anime` type is supported!"
            )

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

            emb = generate_media_embed(results[0], ctx.channel.is_nsfw())
            await ctx.send(embed=emb)

    @commands.command()
    # TODO: use typing.Literal for media_type with dpy 2.x
    async def random(self, ctx: commands.Context, media_type: str, *, genre: str):
        """Fetch a random anime or manga based on input genre!

        **Supported Genres:**
            - Action, Adventure, Comedy, Drama, Ecchi
            - Fantasy, Hentai, Horror, Mahou Shoujo, Mecha
            - Music, Mystery, Psychological, Romance, Schi-Fi
            - Slice of Life, Sports, Supernatural, Thriller

        You can use any of the search tags supported on Anilist instead of any of above genres!
        """
        if media_type.lower() not in ["anime", "manga"]:
            return await ctx.send(
                "You provided invalid media type! Only `manga` or `anime` type is supported!"
            )

        async with ctx.typing():
            get_format = {
                "anime": ["TV", "TV_SHORT", "MOVIE", "OVA", "ONA"],
                "manga": ["MANGA", "NOVEL", "ONE_SHOT"]
            }

            results = await MediaData.request(
                self.session,
                query=GENRE_SCHEMA,
                page=1,
                perPage=1,
                type=media_type.upper(),
                genre=genre,
                format_in=get_format[media_type.lower()]
            )
            if type(results) is str:
                results = await MediaData.request(
                    self.session,
                    query=TAG_SCHEMA,
                    page=1,
                    perPage=1,
                    type=media_type.upper(),
                    tag=genre,
                    format_in=get_format[media_type.lower()]
                )

            if type(results) is str:
                return await ctx.send(
                    f"Could not find a random {media_type} from the given genre or tag.\n"
                    "See if its valid as per AniList or try again with different genre/tag."
                )

            emb = generate_media_embed(results[0], ctx.channel.is_nsfw())
            await ctx.send(embed=emb)

    @commands.command()
    async def character(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch info on a anime/manga character from given query!"""
        async with ctx.typing():
            results = await CharacterData.request(
                self.session,
                query=CHARACTER_SCHEMA,
                page=1,
                perPage=15,
                search=query,
                sort="SEARCH_MATCH"
            )
            if type(results) is str:
                return await ctx.send(results)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = generate_character_embed(page)
                emb.set_footer(text=f"Powered by AniList • Page {i} of {len(results)}")
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command()
    async def studio(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch info on an animation studio from given query!"""
        ...
