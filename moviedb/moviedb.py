from operator import attrgetter
from typing import Any, List, cast

import aiohttp
import discord
from discord.app_commands import describe
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.commands import Context
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .api.base import CDN_BASE, MediaNotFound
from .api.details import MovieDetails, TVShowDetails
from .api.person import Person
from .api.suggestions import MovieSuggestions, TVShowSuggestions
from .constants import TMDB_ICON
from .converter import MovieFinder, PersonFinder, TVShowFinder
from .utils import (
    make_movie_embed,
    make_person_embed,
    make_suggestmovies_embed,
    make_suggestshows_embed,
    make_tvshow_embed,
    parse_credits,
)

COLOR = discord.Colour(0xC57FFF)


class MovieDB(commands.GroupCog, group_name="imdb"):
    """Get summarized info about a movie or TV show/series."""

    __authors__ = "<@306810730055729152>"
    __version__ = "4.2.0"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        await self.session.close()

    def format_help_for_context(self, ctx: Context) -> str:  # Thanks Sinbad!
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Author(s):** {self.__authors__}\n"
            f"**Cog version:** {self.__version__}"
        )

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete"""
        pass

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=["actor", "director"])
    @describe(name="Enter celebrity actor/director name. Be specific for accurate results!")
    async def celebrity(self, ctx: Context, *, name: PersonFinder):
        """Get info about a movie/tvshow celebrity or crew!"""
        await ctx.typing()
        if isinstance(name, MediaNotFound):
            return await ctx.send(str(name))

        data = cast(Person, name)
        embeds: List[discord.Embed] = []
        emb1 = make_person_embed(data, COLOR)
        if (acting := data.combined_credits) and acting.cast:
            emb2 = discord.Embed(colour=emb1.colour)
            emb2.set_author(
                name=f"{data.name}’s Acting Roles", icon_url=data.person_image, url=emb1.url
            )
            emb2.description = "\n".join(
                z.pretty_format
                for z in sorted(acting.cast[:20], key=attrgetter("year"), reverse=True)
            )
            if len(acting.cast) > 20:
                emb2.set_footer(
                    text=f"and {len(acting.cast) - 20} more! • Sorted from recent to oldest!",
                    icon_url=TMDB_ICON
                )
            embeds.append(emb2)
        if (acting := data.combined_credits) and acting.crew:
            emb3 = discord.Embed(colour=emb1.colour)
            emb3.set_author(
                name=f"{data.name}’s Production Roles", icon_url=data.person_image, url=emb1.url
            )
            emb3.description = "\n".join(
                crew.pretty_format
                for crew in sorted(acting.crew[:20], key=attrgetter("year"), reverse=True)
            )
            if len(acting.crew) > 20:
                emb3.set_footer(
                    text=f"and {len(acting.crew) - 20} more! • Sorted from recent to oldest!",
                    icon_url=TMDB_ICON
                )
            embeds.append(emb3)
        embeds.insert(0, emb1)
        await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=90)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    @describe(movie="Provide name of the movie. Try to be specific for accurate results!")
    async def movie(self, ctx: Context, *, movie: MovieFinder):
        """Show various info about a movie."""
        await ctx.typing()
        if isinstance(movie, MediaNotFound):
            return await ctx.send(str(movie))

        data = cast(MovieDetails, movie)
        emb1 = make_movie_embed(data, COLOR)
        emb2 = discord.Embed(colour=COLOR, title=data.title)
        emb2.url = f"https://www.themoviedb.org/movie/{data.id}"
        emb2.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
        if data.production_companies:
            emb2.add_field(name="Production Companies:", value=data.all_production_companies)
        if data.production_countries:
            emb2.add_field(
                name="Production Countries:",
                value=data.all_production_countries,
                inline=False,
            )
        if data.tagline:
            emb2.add_field(name="Tagline:", value=data.tagline, inline=False)

        celebrities = []
        if data.credits:
            emb2.set_footer(text="See next page to see the celebrity cast!", icon_url=TMDB_ICON)
            celebrities = parse_credits(
                data.credits,
                colour=COLOR,
                tmdb_id=f"movie/{data.id}",
                title=data.title,
            )
        await menu(ctx, [emb1, emb2] + celebrities, DEFAULT_CONTROLS, timeout=90)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=["tv", "tvseries"], fallback='search')
    @describe(tv_show="Provide name of TV show. Try to be specific for accurate results!")
    async def tvshow(self, ctx: Context, *, tv_show: TVShowFinder):
        """Show various info about a TV show/series."""
        await ctx.typing()
        if isinstance(tv_show, MediaNotFound):
            return await ctx.send(str(tv_show))

        data = cast(TVShowDetails, tv_show)
        emb1 = make_tvshow_embed(data, COLOR)
        emb2 = discord.Embed(colour=COLOR, title=data.name)
        emb2.url = f"https://www.themoviedb.org/tv/{data.id}"
        emb2.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
        if production_countries := data.production_countries:
            emb2.add_field(
                name="Production Countries:",
                value=", ".join([m.name for m in production_countries]),
            )
        if production_companies := data.production_companies:
            emb2.add_field(
                name="Production Companies:",
                value=", ".join([m.name for m in production_companies]),
                inline=False,
            )
        if data.tagline:
            emb2.add_field(name="Tagline:", value=data.tagline, inline=False)

        celebrities = []
        if data.credits:
            emb2.set_footer(text="See next page for series' celebrity cast!", icon_url=TMDB_ICON)
            celebrities = parse_credits(
                data.credits,
                colour=COLOR,
                tmdb_id=f"tv/{data.id}",
                title=data.name,
            )
        await menu(ctx, [emb1, emb2] + celebrities, DEFAULT_CONTROLS, timeout=90)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=['suggestmovie'])
    @describe(movie="Provide name of the movie. Try to be specific in your query!")
    async def suggestmovies(self, ctx: Context, *, movie: MovieFinder):
        """Get similar movies suggestions based on the given movie name."""
        await ctx.typing()
        if isinstance(movie, MediaNotFound):
            return await ctx.send(str(movie))

        embeds: List[discord.Embed] = []
        output = cast(List[MovieSuggestions], movie)
        for i, data in enumerate(output, start=1):
            colour = COLOR
            footer = f"Page {i} of {len(output)}"
            embeds.append(make_suggestmovies_embed(data, colour, footer))
        await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=90)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=['suggestshow'])
    @describe(tv_show="Provide name of TV show. Try to be specific for accurate results!")
    async def suggestshows(self, ctx: Context, *, tv_show: TVShowFinder):
        """Get similar TV show suggestions from the given TV series name."""
        await ctx.typing()
        if isinstance(tv_show, MediaNotFound):
            return await ctx.send(str(tv_show))

        embeds: List[discord.Embed] = []
        output = cast(List[TVShowSuggestions], tv_show)
        for i, data in enumerate(output, start=1):
            colour = COLOR
            footer = f"Page {i} of {len(output)}"
            embeds.append(make_suggestshows_embed(data, colour, footer))
        await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=90)
        return
