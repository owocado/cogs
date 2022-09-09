from typing import Any, List, cast

import aiohttp
import discord
from discord.app_commands import describe
from redbot.core import commands
from redbot.core.commands import Context
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .api import MovieDetails, MovieSuggestions, TVShowDetails, TVShowSuggestions
from .constants import CDN_BASE, MediaNotFound
from .converter import MovieFinder, TVShowFinder
from .embed_utils import (
    make_movie_embed,
    parse_credits,
    make_suggestmovies_embed,
    make_suggestshows_embed,
    make_tvshow_embed
)


class MovieDB(commands.Cog):
    """Get summarized info about a movie or TV show/series."""

    __authors__ = "ow0x"
    __version__ = "4.0.0"

    def format_help_for_context(self, ctx: Context) -> str:  # Thanks Sinbad!
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Author(s):** {self.__authors__}\n"
            f"**Cog version:** {self.__version__}"
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.session = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        await self.session.close()

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    async def cog_check(self, ctx: Context) -> bool:
        if not ctx.guild:
            return True

        my_perms = ctx.channel.permissions_for(ctx.guild.me)
        return my_perms.embed_links and my_perms.read_message_history

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    @describe(movie="Provide name of the movie. Try to be specific so I can show accurate result!")
    async def movie(self, ctx: Context, *, movie: MovieFinder):
        """Show various info about a movie."""
        async with ctx.typing():
            # api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
            # data = await MovieDetails.request(ctx.bot.session, api_key, query)
            if isinstance(movie, MediaNotFound):
                return await ctx.send(str(movie))

            data = cast(MovieDetails, movie)
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

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=["tv", "tvseries"], fallback='search')
    @describe(tv_show="Provide name of TV show. Try to be specific so I can show accurate result!")
    async def tvshow(self, ctx: Context, *, tv_show: TVShowFinder):
        """Show various info about a TV show/series."""
        async with ctx.typing():
            # api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
            # data = await TVShowDetails.request(ctx.bot.session, api_key, query)
            if isinstance(tv_show, MediaNotFound):
                return await ctx.send(str(tv_show))

            data = cast(TVShowDetails, tv_show)
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
                    tmdb_id=f"tv/{data.id}",
                    title=data.name,
                )

        await menu(ctx, [emb1, emb2] + celebrities, DEFAULT_CONTROLS, timeout=120)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=['suggestmovie'])
    @describe(movie="Provide name of the movie. Try to be specific in your query!")
    async def suggestmovies(self, ctx: Context, *, movie: MovieFinder):
        """Get similar movies suggestions based on the given movie name."""
        async with ctx.channel.typing():
            # api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
            # output = await MovieSuggestions.request(ctx.bot.session, api_key, query)
            if isinstance(movie, MediaNotFound):
                return await ctx.send(str(movie))

            pages = []
            output = cast(List[MovieSuggestions], movie)
            for i, data in enumerate(output, start=1):
                colour = await ctx.embed_colour()
                footer = f"Page {i} of {len(output)}"
                pages.append(make_suggestmovies_embed(data, colour, footer))

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=['suggestshow'])
    @describe(tv_show="Provide name of TV show. Try to be specific so I can show accurate result!")
    async def suggestshows(self, ctx: Context, *, tv_show: TVShowFinder):
        """Get similar TV show suggestions from the given TV series name."""
        async with ctx.channel.typing():
            # api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
            # output = await TVShowSuggestions.request(ctx.bot.session, api_key, query)
            if isinstance(tv_show, MediaNotFound):
                return await ctx.send(str(tv_show))

            pages = []
            output = cast(List[TVShowSuggestions], tv_show)
            for i, data in enumerate(output, start=1):
                colour = await ctx.embed_colour()
                footer = f"Page {i} of {len(output)}"
                pages.append(make_suggestshows_embed(data, colour, footer))

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

