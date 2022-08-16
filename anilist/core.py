import asyncio
import logging
import random

import aiohttp
from redbot.core import commands
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .api.character import CharacterData
from .api.constants import GenreCollection
from .api.media import MediaData
from .api.schedule import ScheduleData
from .api.staff import StaffData
from .api.studio import StudioData
from .api.user import UserData
from .embed_maker import (
    do_character_embed,
    do_media_embed,
    do_schedule_embed,
    do_staff_embed,
    do_studio_embed,
    do_user_embed
)
from .schemas import (
    CHARACTER_SCHEMA,
    GENRE_COLLECTION_SCHEMA,
    GENRE_SCHEMA,
    MEDIA_SCHEMA,
    SCHEDULE_SCHEMA,
    STAFF_SCHEMA,
    STUDIO_SCHEMA,
    TAG_SCHEMA,
    USER_SCHEMA
)

log = logging.getLogger("red.owo.anilist")


class Anilist(commands.Cog):
    """Fetch info on anime, manga, character, studio and more from Anilist!"""

    __authors__ = ["<@306810730055729152>"]
    __version__ = "0.4.0"

    def format_help_for_context(self, ctx: commands.Context) -> str: # Thanks Sinbad!
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(self.__authors__)}\n"
            f"**Cog version:**  {self.__version__}"
        )

    def __init__(self, *args, **kwargs):
        self.session = aiohttp.ClientSession()
        self.supported_genres = GenreCollection
        # asyncio.create_task(self.initialize())

    def cog_unload(self) -> None:
        asyncio.create_task(self.session.close())

    # TODO: utilise cog_load with dpy2
    async def initialize(self) -> None:
        fetched_genres = await self.fetch_genres(self.session, GENRE_COLLECTION_SCHEMA)
        log.debug(f"Fetched supported genres from AniList:\n{fetched_genres}")
        if fetched_genres and self.supported_genres != fetched_genres:
            self.supported_genres = fetched_genres

    async def fetch_genres(self, session: aiohttp.ClientSession, query: str):
        try:
            async with session.post("https://graphql.anilist.co", json={"query": query}) as resp:
                if resp.status != 200:
                    return []
                return (await resp.json())["data"]["GenreCollection"]
        except (KeyError, aiohttp.ClientError, asyncio.TimeoutError):
            return []

    async def cog_check(self, ctx: commands.Context) -> bool:
        if ctx.guild:
            my_perms = ctx.channel.permissions_for(ctx.guild.me)
            return my_perms.read_message_history and my_perms.send_messages
        return True

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
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
                emb = do_media_embed(page, ctx.channel.is_nsfw())
                text = f"{emb.footer.text} • Page {i} of {len(results)}"
                emb.set_footer(text=text)
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command(aliases=["manhwa"])
    @commands.bot_has_permissions(embed_links=True)
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
                emb = do_media_embed(page, ctx.channel.is_nsfw())
                emb.set_footer(text=f"{emb.footer.text} • Page {i} of {len(results)}")
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    # TODO: use typing.Literal for media_type with dpy 2.x
    async def trending(self, ctx: commands.Context, media_type: str):
        """Fetch currently trending animes or manga from AniList!"""
        if media_type.lower() not in ["anime", "manga"]:
            return await ctx.send(
                "Invalid media type provided! Only `manga` or `anime` type is supported!"
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

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_media_embed(page, ctx.channel.is_nsfw())
                emb.set_footer(text=f"{emb.footer.text} • Page {i} of {len(results)}")
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    # TODO: use typing.Literal for media_type with dpy 2.x
    async def random(self, ctx: commands.Context, media_type: str, *, genre_or_tag: str = ""):
        """Fetch a random anime or manga based on provided genre or tag!

        **Supported Genres:**
            - Action, Adventure, Comedy, Drama, Ecchi
            - Fantasy, Hentai, Horror, Mahou Shoujo, Mecha
            - Music, Mystery, Psychological, Romance, Schi-Fi
            - Slice of Life, Sports, Supernatural, Thriller

        You can also use any of the search tags supported on Anilist instead of any of above genres!
        """
        if media_type.lower() not in ["anime", "manga"]:
            return await ctx.send(
                "Invalid media type provided! Only `manga` or `anime` type is supported!"
            )

        async with ctx.typing():
            if not genre_or_tag:
                genre_or_tag = random.choice(self.supported_genres)
                await ctx.send(
                    f"Since you didn't provide a genre or tag, I chose a random genre: {genre_or_tag}"
                )

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
                genre=genre_or_tag,
                format_in=get_format[media_type.lower()]
            )
            if type(results) is str:
                results = await MediaData.request(
                    self.session,
                    query=TAG_SCHEMA,
                    page=1,
                    perPage=1,
                    type=media_type.upper(),
                    tag=genre_or_tag,
                    format_in=get_format[media_type.lower()]
                )

            if type(results) is str:
                return await ctx.send(
                    f"Could not find a random {media_type} from the given genre or tag.\n"
                    "See if its valid as per AniList or try again with different genre/tag."
                )

            emb = do_media_embed(results[0], ctx.channel.is_nsfw())
            await ctx.send(embed=emb)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
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
                emb = do_character_embed(page)
                emb.set_footer(text=f"Powered by AniList • Page {i} of {len(results)}")
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def studio(self, ctx: commands.Context, *, name: str) -> None:
        """Fetch info on an animation studio from given name query!"""
        async with ctx.typing():
            results = await StudioData.request(
                self.session,
                query=STUDIO_SCHEMA,
                page=1,
                perPage=15,
                search=name,
            )
            if type(results) is str:
                return await ctx.send(results)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_studio_embed(page)
                emb.set_footer(text=f"Powered by AniList • Page {i} of {len(results)}")
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command()
    async def upcoming(self, ctx: commands.Context, summary_version: bool = False):
        """Fetch list of upcoming animes airing within a day."""
        async with ctx.typing():
            results = await ScheduleData.request(
                self.session,
                query=SCHEDULE_SCHEMA,
                page=1,
                perPage=20,
                notYetAired=True,
                sort="TIME"
            )
            if type(results) is str:
                return await ctx.send(results)

            if not ctx.channel.permissions_for(ctx.me).embed_links or summary_version:
                airing = "\n".join(
                    f"<t:{media.airingAt}:R> • {media.media.title}" for media in results
                )
                await ctx.send(f"Upcoming animes in next **24 to 48 hours**:\n\n{airing}")
                return

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_schedule_embed(page, upcoming=True)
                emb.set_footer(text=f"Powered by AniList • Page {i} of {len(results)}")
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command()
    async def lastaired(self, ctx: commands.Context, summary_version: bool = False):
        """Fetch list of upcoming animes airing within a day."""
        async with ctx.typing():
            results = await ScheduleData.request(
                self.session,
                query=SCHEDULE_SCHEMA,
                page=1,
                perPage=20,
                notYetAired=False,
                sort="TIME_DESC"
            )
            if type(results) is str:
                return await ctx.send(results)

            if not ctx.channel.permissions_for(ctx.me).embed_links or summary_version:
                airing = "\n".join(
                    f"<t:{media.airingAt}:R> • {media.media.title}" for media in results
                )
                await ctx.send(f"Recently aired animes in past **24 to 48 hours**:\n\n{airing}")
                return

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_schedule_embed(page, upcoming=False)
                emb.set_footer(text=f"Powered by AniList • Page {i} of {len(results)}")
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command(aliases=("mangaka", "seiyuu"))
    @commands.bot_has_permissions(embed_links=True)
    async def anistaff(self, ctx: commands.Context, *, name: str):
        """Get info on any manga or anime staff, seiyuu etc."""
        async with ctx.typing():
            results = await StaffData.request(
                self.session,
                query=STAFF_SCHEMA,
                page=1,
                perPage=15,
                search=name,
            )
            if type(results) is str:
                return await ctx.send(results)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_staff_embed(page)
                emb.set_footer(text=f"Powered by AniList • Page {i} of {len(results)}")
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command(aliases=["anilistuser"])
    @commands.bot_has_permissions(embed_links=True)
    async def aniuser(self, ctx: commands.Context, username: str):
        """Get info on AniList user account."""
        async with ctx.typing():
            results = await UserData.request(
                self.session,
                query=USER_SCHEMA,
                page=1,
                perPage=15,
                search=username
            )
            if type(results) is str:
                return await ctx.send(results)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_user_embed(page)
                text = f"{emb.footer.text} • Page {i} of {len(results)}"
                emb.set_footer(text=text)
                pages.append(emb)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)
