import asyncio
from typing import Any, Dict, List, Union

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number as fnum, pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .converter import MovieQueryConverter, TVShowQueryConverter, parse_date, request

API_BASE = "https://api.themoviedb.org/3"
CDN_BASE = "https://image.tmdb.org/t/p/original"


def is_apikey_set():
    async def predicate(ctx: commands.Context) -> bool:
        return bool(await ctx.bot.get_shared_api_tokens("tmdb"))

    return commands.check(predicate)


class MovieDB(commands.Cog):
    """Get summarized info about a movie or TV show/series."""

    __author__ = "ow0x"
    __version__ = "2.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:  # Thanks Sinbad!
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"Author: {self.__author__}\n"
            f"Cog version: {self.__version__}"
        )

    def __init__(self) -> None:
        self.session = aiohttp.ClientSession()

    def cog_unload(self) -> None:
        asyncio.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    @staticmethod
    def movie_embed(colour: discord.Colour, data: Dict[str, Any]) -> discord.Embed:
        embed = discord.Embed(title=data.get("title") or "", colour=colour)
        description = data.get("overview") or ""
        if imdb_id := data.get("imdb_id"):
            description += f"\n\n**[see IMDB page!](https://www.imdb.com/title/{imdb_id})**"
        embed.url = f"https://www.themoviedb.org/movie/{data.get('id', '')}"
        embed.description = description
        # embed.set_image(url=f"{CDN_BASE}{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(url=f"{CDN_BASE}{data.get('poster_path', '/')}")
        if release_date := data.get("release_date"):
            embed.add_field(name="Release Date", value=parse_date(release_date))
        if budget := data.get("budget"):
            embed.add_field(name="Budget", value=f"USD {fnum(budget)}")
        if revenue := data.get("revenue"):
            embed.add_field(name="Revenue", value=f"USD {fnum(revenue)}")
        if runtime := data.get("runtime"):
            embed.add_field(name="Runtime", value=f"{runtime // 60}h {runtime % 60}m")
        if (vote_average := data.get("vote_average")) and (vote_count := data.get("vote_count")):
            if int(vote_average) > 0:
                embed.add_field(
                    name="TMDB Rating",
                    value=f"**{vote_average:.1f}** ⭐ / 10\n({fnum(vote_count)} votes)",
                )
        if spoken_languages := data.get("spoken_languages"):
            embed.add_field(
                name="Spoken languages",
                value=", ".join([m.get("english_name") for m in spoken_languages]),
            )
        if genres := data.get("genres"):
            embed.add_field(name="Genres", value=", ".join([m.get("name") for m in genres]))
        if len(embed.fields) in {5, 8, 11}:
            embed.add_field(name="\u200b", value="\u200b")
        embed.set_footer(
            text="Click arrows to see more info!",
            icon_url="https://i.imgur.com/sSE7Usn.png",
        )
        return embed

    @commands.command(aliases=["moviecast"], usage="movie name or title")
    @is_apikey_set()
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def movie(self, ctx: commands.Context, *, query: MovieQueryConverter):
        """Show various info about a movie."""
        async with ctx.channel.typing():
            api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
            data: Union[int, Dict[str, Any]] = await request(
                f"{API_BASE}/movie/{query}",
                params={"api_key": api_key, "append_to_response": "credits"},
            )
            if type(data) == int:
                await ctx.send(f"⚠ API sent response code: https://http.cat/{data}")
                return
            if not data:
                return await ctx.send("⛔ Could not fetch any data from TMDB API.")

            emb1 = self.movie_embed(await ctx.embed_colour(), data)
            emb2 = discord.Embed(colour=await ctx.embed_colour(), title=data.get("title") or "")
            emb2.url = f"https://www.themoviedb.org/movie/{data.get('id', '')}"
            emb2.set_image(url=f"{CDN_BASE}{data.get('backdrop_path', '/')}")
            if production_companies := data.get("production_companies"):
                emb2.add_field(
                    name="Production Companies",
                    value=", ".join([m.get("name") for m in production_companies]),
                )
            if production_countries := data.get("production_countries"):
                emb2.add_field(
                    name="Production Countries",
                    value=", ".join([m.get("name") for m in production_countries]),
                    inline=False,
                )
            if tagline := data.get("tagline"):
                emb2.add_field(name="Tagline", value=tagline, inline=False)

            celebrities = []
            if cast_data := data.get("credits", {}).get("cast"):
                emb2.set_footer(text="ℹ See next page to see the celebrities cast!")
                celebrities = self.parse_credits(
                    f"movie/{data['id']}", data.get("original_title"), cast_data
                )

        await menu(ctx, [emb1, emb2] + celebrities, DEFAULT_CONTROLS, timeout=120)

    @staticmethod
    def parse_credits(
        tmdb_id: int, title: str, cast_data: List[Dict[str, Any]]
    ) -> List[discord.Embed]:
        GENDERS_MAP = {"0": "", "1": "♀", "2": "♂"}
        pretty_cast = "\n".join(
            f"**`{i:>2}.`**  [{actor_obj.get('original_name')}]"
            f"(https://www.themoviedb.org/person/{actor_obj['id']})"
            f" {GENDERS_MAP[str(actor_obj.get('gender', 0))]}"
            f" as **{actor_obj.get('character') or '???'}**"
            for i, actor_obj in enumerate(cast_data, 1)
        )

        pages = []
        all_pages = list(pagify(pretty_cast, page_length=1500))
        for i, page in enumerate(all_pages, start=1):
            emb = discord.Embed(colour=discord.Colour.random(), description=page, title=title)
            emb.url = f"https://www.themoviedb.org/{tmdb_id}"
            emb.set_footer(
                text=f"Celebrities Cast • Page {i} of {len(all_pages)}",
                icon_url="https://i.imgur.com/sSE7Usn.png",
            )
            pages.append(emb)

        return pages

    @staticmethod
    def tvshow_embed(colour: discord.Colour, data: Dict[str, Any]) -> discord.Embed:
        summary = (
            f"**Series status:**  {data.get('status') or 'Unknown'} ({data.get('type')})\n"
        )
        if runtime := data.get("episode_run_time"):
            summary += f"**Average episode runtime:**  {runtime[0]} minutes\n"
        embed = discord.Embed(
            title=data.get("name") or "",
            description=f"{data.get('overview') or ''}\n\n{summary}",
            colour=colour,
        )
        embed.url = f"https://www.themoviedb.org/tv/{data.get('id')}"
        # embed.set_image(url=f"{CDN_BASE}{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(url=f"{CDN_BASE}{data.get('poster_path', '/')}")
        if first_air_date := data.get("first_air_date"):
            embed.add_field(name="First Air Date", value=parse_date(first_air_date))
        if last_air_date := data.get("last_air_date"):
            embed.add_field(name="Last Air Date", value=parse_date(last_air_date))
        if seasons_count := data.get("number_of_seasons"):
            embed.add_field(
                name="Seasons",
                value=f"{seasons_count} ({data.get('number_of_episodes')} episodes)",
            )
        if created_by := data.get("created_by", {}):
            embed.add_field(name="Creators", value=", ".join([m.get("name") for m in created_by]))
        if genres := data.get("genres", []):
            embed.add_field(name="Genres", value=", ".join([m.get("name") for m in genres]))
        if (vote_average := data.get("vote_average")) and (vote_count := data.get("vote_count")):
            if int(vote_average) > 0:
                embed.add_field(
                    name="TMDB Rating",
                    value=f"**{vote_average:.1f}** ⭐ / 10\n({fnum(vote_count)} votes)",
                )
        if networks := data.get("networks"):
            embed.add_field(name="Networks", value=", ".join([m.get("name") for m in networks]))
        if spoken_languages := data.get("spoken_languages", []):
            embed.add_field(
                name="Spoken languages",
                value=", ".join([m.get("english_name") for m in spoken_languages]),
            )
        if seasons_data := data.get("seasons"):
            seasons_meta = "\n".join(
                f"**`[{i:>2}]`** {tv.get('name')}"
                f"{parse_date(tv.get('air_date'), prefix=', first aired ')}"
                f"  ({tv.get('episode_count', 0)} episodes)"
                for i, tv in enumerate(seasons_data, start=1)
            )
            embed.add_field(name="Seasons summary", value=seasons_meta, inline=False)
        if next_ep := data.get("next_episode_to_air"):
            next_airing = "N/A"
            if next_ep.get("air_date"):
                next_airing = parse_date(next_ep["air_date"])
            next_episode_info = (
                f"**S{next_ep.get('season_number', 0)}E{next_ep.get('episode_number', 0)}: "
                f"{next_ep.get('name', 'N/A')}**\n`next airing:` {next_airing}"
            )
            embed.add_field(name="Next episode info", value=next_episode_info, inline=False)
        in_production = f"In production? ✅ Yes • " if data.get("in_production") else ""
        embed.set_footer(
            text=f"{in_production}Click on arrows to see more info!",
            icon_url="https://i.imgur.com/sSE7Usn.png",
        )
        return embed

    @commands.command(aliases=["tv"], usage="tvshow name or title")
    @is_apikey_set()
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def tvshow(self, ctx: commands.Context, *, query: TVShowQueryConverter):
        """Show various info about a TV show/series."""
        async with ctx.channel.typing():
            api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
            data: Union[int, Dict[str, Any]] = await request(
                f"{API_BASE}/tv/{query}",
                params={"api_key": api_key, "append_to_response": "credits"},
            )
            if type(data) == int:
                await ctx.send(f"⚠ API sent response code: https://http.cat/{data}")
                return
            if not data:
                return await ctx.send("⛔ Could not connect to TMDB API.")

            emb1 = self.tvshow_embed(await ctx.embed_colour(), data)
            emb2 = discord.Embed(colour=await ctx.embed_colour(), title=data.get("name") or "")
            emb2.url = f"https://www.themoviedb.org/tv/{data.get('id')}"
            if backdrop_path := data.get("backdrop_path"):
                emb2.set_image(url=f"{CDN_BASE}{backdrop_path or '/'}")
            if production_countries := data.get("production_countries"):
                emb2.add_field(
                    name="Production Countries",
                    value=", ".join([m.get("name") for m in production_countries]),
                )
            if production_companies := data.get("production_companies"):
                emb2.add_field(
                    name="Production Companies",
                    value=", ".join([m.get("name") for m in production_companies]),
                    inline=False,
                )
            if tagline := data.get("tagline"):
                emb2.add_field(name="Tagline", value=tagline, inline=False)

            celebrities = []
            if cast_data := data.get("credits", {}).get("cast"):
                emb2.set_footer(text="ℹ See next page to see the celebrities cast!")
                celebrities = self.parse_credits(
                    f"tv/{data['id']}", data.get("original_name"), cast_data
                )

        await menu(ctx, [emb1, emb2] + celebrities, DEFAULT_CONTROLS, timeout=120)

    @staticmethod
    def suggestmovies_embed(
        colour: discord.Colour, footer: str, data: Dict[str, Any]
    ) -> discord.Embed:
        embed = discord.Embed(
            colour=colour,
            title=data.get("title") or "",
            description=data.get("overview") or "",
        )
        embed.url = f"https://www.themoviedb.org/movie/{data.get('id', '')}"
        embed.set_image(url=f"{CDN_BASE}{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(url=f"{CDN_BASE}{data.get('poster_path', '/')}")
        if release_date := data.get("release_date"):
            embed.add_field(name="Release Date", value=parse_date(release_date))
        if (vote_average := data.get("vote_average")) and (vote_count := data.get("vote_count")):
            if int(vote_average) > 0:
                embed.add_field(
                    name="TMDB Rating",
                    value=f"**{vote_average:.1f}** ⭐ / 10\n({fnum(vote_count)} votes)",
                )
        embed.set_footer(text=footer, icon_url="https://i.imgur.com/sSE7Usn.png")
        return embed

    @commands.command(aliases=["suggestmovie"], usage="movie name")
    @is_apikey_set()
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def suggestmovies(self, ctx: commands.Context, *, query: MovieQueryConverter):
        """Get similar movies suggestions based on the given movie title query."""
        async with ctx.channel.typing():
            api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
            output = await request(
                f"{API_BASE}/movie/{query}/recommendations", params={"api_key": api_key}
            )
            if type(output) == int:
                await ctx.send(f"⚠ API sent response code: https://http.cat/{output}")
                return
            if not output:
                return await ctx.send("⛔ Could not connect to TMDB API.")
            if not output.get("results"):
                return await ctx.send("No recommendations found related to that movie.")

            pages = []
            for i, data in enumerate(output.get("results"), start=1):
                colour = await ctx.embed_colour()
                footer = f"Page {i} of {len(output['results'])}"
                pages.append(self.suggestmovies_embed(colour, footer, data))

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)

    @staticmethod
    def suggestshows_embed(
        colour: discord.Colour, footer: str, data: Dict[str, Any]
    ) -> discord.Embed:
        embed = discord.Embed(
            title=data.get("name") or "", description=data.get("overview") or "", colour=colour
        )
        embed.url = f"https://www.themoviedb.org/tv/{data.get('id', '')}"
        embed.set_image(url=f"{CDN_BASE}{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(url=f"{CDN_BASE}{data.get('poster_path', '/')}")
        if first_air_date := data.get("first_air_date"):
            embed.add_field(name="First Air Date", value=parse_date(first_air_date))
        if (vote_average := data.get("vote_average")) and (vote_count := data.get("vote_count")):
            if int(vote_average) > 0:
                embed.add_field(
                    name="TMDB Rating",
                    value=f"**{vote_average:.1f}** ⭐ / 10 ({fnum(vote_count)} votes)",
                )
        embed.set_footer(text=footer, icon_url="https://i.imgur.com/sSE7Usn.png")
        return embed

    @commands.command(aliases=["suggestseries", "suggestshow"], usage="tv series name/title")
    @is_apikey_set()
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def suggestshows(self, ctx: commands.Context, *, query: TVShowQueryConverter):
        """Get similar TV show suggestions from the given TV series title query."""
        async with ctx.channel.typing():
            api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
            output = await request(
                f"{API_BASE}/tv/{query}/recommendations", params={"api_key": api_key}
            )
            if type(output) == int:
                await ctx.send(f"⚠ API sent response code: https://http.cat/{output}")
                return
            if not output:
                return await ctx.send("⛔ Could not connect to TMDB API.")

            if not output.get("results"):
                return await ctx.send("No recommendations found related to that TV show.")

            pages = []
            for i, data in enumerate(output["results"], start=1):
                colour = await ctx.embed_colour()
                footer = f"Page {i} of {len(output['results'])}"
                pages.append(self.suggestshows_embed(colour, footer, data))

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=120)
