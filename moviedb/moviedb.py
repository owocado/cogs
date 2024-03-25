from typing import Annotated, Any, List, Tuple, cast

import discord
from discord.app_commands import describe
from redbot.core import commands
from redbot.core.commands import Context
from redbot.core.utils.views import BaseMenu, ListPages

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


class MovieDB(commands.Cog):
    """Get summarized info about a movie or TV show/series."""

    __authors__ = "<@306810730055729152>"
    __version__ = "4.3.0"

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
    @commands.hybrid_command(aliases=["actor", "director", "celeb"])
    @describe(name="Enter celebrity actor/director name. Be specific for accurate results!")
    async def celebrity(
        self, ctx: Context, *, name: Annotated[Tuple[discord.Message, Person], PersonFinder]
    ) -> None:
        """Get info about a movie/tvshow celebrity or crew!"""
        if ctx.interaction:
            return
        await ctx.defer(ephemeral=True)
        message, data = name
        emb1 = make_person_embed(data, COLOR)
        try:
            await message.edit(content=None, embed=emb1)
        except Exception:
            await ctx.send(embed=emb1)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    @describe(movie="Provide name of the movie. Try to be specific for accurate results!")
    async def movie(self, ctx: Context, *, movie: MovieFinder):
        """Show various info about a movie."""
        await ctx.typing()
        if isinstance(movie, MediaNotFound):
            return await ctx.send(str(movie))

        embeds: List[discord.Embed] = []
        data = cast(MovieDetails, movie)
        embeds.append(make_movie_embed(data, COLOR))
        emb2 = discord.Embed(colour=COLOR, title=data.title)
        emb2.url = f"https://themoviedb.org/movie/{data.id}"
        if data.backdrop_path:
            emb2.set_image(url=f"{CDN_BASE}{data.backdrop_path}")
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
        if bool(emb2.fields) or bool(emb2.image):
            embeds.append(emb2)

        if data.credits:
            emb2.set_footer(text="See next page to see the celebrity cast!", icon_url=TMDB_ICON)
            celebrities_embed = parse_credits(
                data.credits,
                colour=COLOR,
                tmdb_id=f"movie/{data.id}",
                title=data.title,
            )
            embeds.extend(celebrities_embed)
        await BaseMenu(ListPages(embeds), timeout=120, ctx=ctx).start(ctx, ephemeral=True)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=["tv", "tvseries"], fallback="search")
    @describe(tv_show="Provide name of TV show. Try to be specific for accurate results!")
    async def tvshow(self, ctx: Context, *, tv_show: TVShowFinder):
        """Show various info about a TV show/series."""
        await ctx.typing()
        if isinstance(tv_show, MediaNotFound):
            return await ctx.send(str(tv_show))

        embeds: List[discord.Embed] = []
        data = cast(TVShowDetails, tv_show)
        embeds.append(make_tvshow_embed(data, COLOR))
        emb2 = discord.Embed(colour=COLOR, title=data.name)
        emb2.url = f"https://themoviedb.org/tv/{data.id}"
        if data.backdrop_path:
            emb2.set_image(url=f"{CDN_BASE}{data.backdrop_path}")
        if production_countries := data.production_countries:
            emb2.add_field(
                name="Production Countries:",
                value="\n".join([m.name for m in production_countries]),
            )
        if production_companies := data.production_companies:
            emb2.add_field(
                name="Production Companies:",
                value=", ".join([m.name for m in production_companies]),
                inline=False,
            )
        if data.tagline:
            emb2.add_field(name="Tagline:", value=data.tagline, inline=False)
        if bool(emb2.fields) or bool(emb2.image):
            embeds.append(emb2)

        if data.credits:
            emb2.set_footer(text="See next page for series' celebrity cast!", icon_url=TMDB_ICON)
            celebrities_embed = parse_credits(
                data.credits,
                colour=COLOR,
                tmdb_id=f"tv/{data.id}",
                title=data.name,
            )
            embeds.extend(celebrities_embed)
        await BaseMenu(ListPages(embeds), timeout=120, ctx=ctx).start(ctx, ephemeral=True)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=["suggestmovie"])
    @describe(movie="Provide name of the movie. Try to be specific in your query!")
    async def suggestmovies(self, ctx: Context, *, movie: MovieFinder):
        """Get similar movies suggestions based on the given movie name."""
        await ctx.typing()
        if isinstance(movie, MediaNotFound):
            return await ctx.send(str(movie))

        pages: List[discord.Embed] = []
        output = cast(List[MovieSuggestions], movie)
        for i, data in enumerate(output, start=1):
            colour = COLOR
            footer = f"Page {i} of {len(output)}"
            pages.append(make_suggestmovies_embed(data, colour, footer))
        await BaseMenu(ListPages(pages), timeout=120, ctx=ctx).start(ctx, ephemeral=True)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=["suggestshow"])
    @describe(tv_show="Provide name of TV show. Try to be specific for accurate results!")
    async def suggestshows(self, ctx: Context, *, tv_show: TVShowFinder):
        """Get similar TV show suggestions from the given TV series name."""
        await ctx.typing()
        if isinstance(tv_show, MediaNotFound):
            return await ctx.send(str(tv_show))

        pages: List[discord.Embed] = []
        output = cast(List[TVShowSuggestions], tv_show)
        for i, data in enumerate(output, start=1):
            colour = COLOR
            footer = f"Page {i} of {len(output)}"
            pages.append(make_suggestshows_embed(data, colour, footer))
        await BaseMenu(ListPages(pages), timeout=120, ctx=ctx).start(ctx, ephemeral=True)
        return
