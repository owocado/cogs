import asyncio

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .api import MovieDetails, MovieSuggestions, TVShowDetails, TVShowSuggestions
from .constants import MediaNotFound
from .converter import MovieFinder, TVShowFinder
from .embed_utils import (
    make_movie_embed,
    parse_credits,
    make_suggestmovies_embed,
    make_suggestshows_embed,
    make_tvshow_embed
)

API_BASE = "https://api.themoviedb.org/3"
CDN_BASE = "https://image.tmdb.org/t/p/original"


def is_apikey_set():
    async def predicate(ctx: commands.Context) -> bool:
        return bool(await ctx.bot.get_shared_api_tokens("tmdb"))

    return commands.check(predicate)


class MovieDB(commands.Cog):
    """Get summarized info about a movie or TV show/series."""

    __authors__ = "ow0x"
    __version__ = "3.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:  # Thanks Sinbad!
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Author(s):** {self.__authors__}\n"
            f"**Cog version:** {self.__version__}"
        )

    session = aiohttp.ClientSession()

    def cog_unload(self) -> None:
        if self.session:
            asyncio.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    @commands.command(aliases=["moviecast"])
    @is_apikey_set()
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def movie(self, ctx: commands.Context, *, query: MovieFinder):
        """Show various info about a movie."""
        async with ctx.typing():
            api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
            data = await MovieDetails.request(self.session, api_key, query)
            if isinstance(data, MediaNotFound):
                return await ctx.send(str(data))

            emb1 = make_movie_embed(data, await ctx.embed_colour())
            emb2 = discord.Embed(colour=await ctx.embed_colour(), title=data.title)
            emb2.url = f"https://www.themoviedb.org/movie/{data.id}"
            emb2.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
            if data.production_companies:
                emb2.add_field(name="Production Companies", value=data.all_production_companies)
            if data.production_countries:
                emb2.add_field(
                    name="Production Countries",
                    value=data.all_production_countries,
                    inline=False,
                )
            if data.tagline:
                emb2.add_field(name="Tagline", value=data.tagline, inline=False)

            celebrities = []
            if data.credits:
                emb2.set_footer(
                    text="See next page to see the celebrity cast!",
                    icon_url="https://i.imgur.com/sSE7Usn.png",
                )
                celebrities = parse_credits(
                    data.credits,
                    colour=await ctx.embed_colour(),
                    tmdb_id=f"movie/{data.id}",
                    title=data.title,
                )

        await menu(ctx, [emb1, emb2] + celebrities, DEFAULT_CONTROLS, timeout=120)

    @commands.command(aliases=["tv", "tvseries"])
    @is_apikey_set()
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def tvshow(self, ctx: commands.Context, *, query: TVShowFinder):
        """Show various info about a TV show/series."""
        async with ctx.typing():
            api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
            data = await TVShowDetails.request(self.session, api_key, query)
            if isinstance(data, MediaNotFound):
                return await ctx.send(str(data))

            emb1 = make_tvshow_embed(data, await ctx.embed_colour())
            emb2 = discord.Embed(colour=await ctx.embed_colour(), title=data.name)
            emb2.url = f"https://www.themoviedb.org/tv/{data.id}"
            emb2.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
            if production_countries := data.production_countries:
                emb2.add_field(
                    name="Production Countries",
                    value=", ".join([m.name for m in production_countries]),
                )
            if production_companies := data.production_companies:
                emb2.add_field(
                    name="Production Companies",
                    value=", ".join([m.name for m in production_companies]),
                    inline=False,
                )
            if data.tagline:
                emb2.add_field(name="Tagline", value=data.tagline, inline=False)

            celebrities = []
            if data.credits:
                emb2.set_footer(
                    text="See next page to see this series' celebrity cast!",
                    icon_url="https://i.imgur.com/sSE7Usn.png",
                )
                celebrities = parse_credits(
                    data.credits,
                    colour=await ctx.embed_colour(),
                    tmdb_id=data.id,
                    title=data.name,
                )

        await menu(ctx, [emb1, emb2] + celebrities, DEFAULT_CONTROLS, timeout=120)

    @commands.command(aliases=["suggestmovie"])
    @is_apikey_set()
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def suggestmovies(self, ctx: commands.Context, *, query: MovieFinder):
        """Get similar movies suggestions based on the given movie title query."""
        async with ctx.channel.typing():
            api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
            output = await MovieSuggestions.request(self.session, api_key, query)
            if isinstance(output, MediaNotFound):
                return await ctx.send(str(output))

            pages = []
            for i, data in enumerate(output, start=1):
                colour = await ctx.embed_colour()
                footer = f"Page {i} of {len(output)}"
                pages.append(make_suggestmovies_embed(data, colour, footer))

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.command(aliases=["suggestseries", "suggestshow"])
    @is_apikey_set()
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def suggestshows(self, ctx: commands.Context, *, query: TVShowFinder):
        """Get similar TV show suggestions from the given TV series title query."""
        async with ctx.channel.typing():
            api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
            output = await TVShowSuggestions.request(self.session, api_key, query)
            if isinstance(output, MediaNotFound):
                return await ctx.send(str(output))

            pages = []
            for i, data in enumerate(output, start=1):
                colour = await ctx.embed_colour()
                footer = f"Page {i} of {len(output)}"
                pages.append(make_suggestshows_embed(data, colour, footer))

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)
