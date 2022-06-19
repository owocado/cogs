import asyncio
from contextlib import suppress
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import aiohttp
import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, close_menu, menu

API_BASE = "https://api.themoviedb.org/3"
CDN_BASE = "https://image.tmdb.org/t/p/original"

def is_apikey_set():
    async def predicate(ctx):
        return bool(await ctx.bot.get_shared_api_tokens("tmdb"))
    return commands.check(predicate)


class MovieDB(commands.Cog):
    """Get summarized info about a movie or TV show/series."""

    __author__ = "ow0x"
    __version__ = "1.2.0"

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
    def _parse_date(date_string: str, style: str = "R") -> str:
        try:
            date_obj = datetime.strptime(date_string, "%Y-%m-%d")
            return f"<t:{int(date_obj.timestamp())}:{style}>"
        # Future proof it in case API changes date string
        except ValueError:
            return ""

    async def get(self, url: str, params: dict):
        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
        except asyncio.TimeoutError:
            return None

    async def fetch_movie_id(
        self, ctx: commands.Context, api_key: str, query: str
    ) -> Optional[int]:
        data = await self.get(f"{API_BASE}/search/movie", {"api_key": api_key, "query": query})
        if not data:
            return None

        if not data.get("results") or len(data.get("results")) == 0:
            return None
        if len(data.get("results")) == 1:
            return data.get("results")[0].get("id")

        # https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
        items = "\n".join(
            f"**{i}.**  {v.get('title', 'N/A')} "
            f"({self._parse_date(v.get('release_date', ''), 'D')})"
            for i, v in enumerate(data["results"], start=1)
        )
        prompt = await ctx.send(
            f"Found multiple results. Please pick one from below:\n\n"
            f"{items.replace('(<t::D>)', '').replace('()', '')}"
        )

        def check(msg: discord.Message) -> bool:
            return bool(
                msg.content.isdigit()
                and int(msg.content) in range(len(items) + 1)
                and msg.author.id == ctx.author.id
                and msg.channel.id == ctx.channel.id
            )

        try:
            choice = await ctx.bot.wait_for("message", timeout=60, check=check)
        except asyncio.TimeoutError:
            choice = None
        if choice is None or choice.content.strip() == "0":
            with suppress(discord.NotFound, discord.HTTPException):
                await prompt.edit(content="No choice was selected. Operation cancelled!")
            return 0

        with suppress(discord.NotFound, discord.HTTPException):
            await prompt.delete()
        return data["results"][int(choice.content.strip()) - 1].get("id")

    def movie_embed(self, colour: discord.Colour, data: Dict[str, Any]) -> discord.Embed:
        embed = discord.Embed(title=data.get("title") or "", colour=colour)
        description = data.get("overview", "")
        if data.get("imdb_id"):
            description += f"\n\n[see IMDB page!](https://www.imdb.com/title/{data['imdb_id']})"
        embed.url = f"https://www.themoviedb.org/movie/{data.get('id', '')}"
        embed.description = description
        # embed.set_image(url=f"{CDN_BASE}{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(url=f"{CDN_BASE}{data.get('poster_path', '/')}")
        if data.get("release_date"):
            embed.add_field(name="Release Date", value=self._parse_date(data["release_date"]))
        if data.get("budget", 0) > 0:
            embed.add_field(name="Budget", value=f'{data.get("budget", 0):,} USD')
        if data.get("revenue", 0) > 0:
            embed.add_field(name="Revenue", value=f'{data.get("revenue", 0):,} USD')
        if data.get("runtime", 0) > 0:
            embed.add_field(
                name="Runtime", value=f"{data['runtime'] // 60}h {data['runtime'] % 60}m"
            )
        if data.get("vote_average", 0.0) > 0.0 and data.get("vote_count", 0) > 0:
            embed.add_field(
                name="TMDB Rating",
                value=f"**{data['vote_average']:.1f}** ⭐ / 10\n({data['vote_count']:,} votes)",
            )
        if data.get("spoken_languages"):
            embed.add_field(
                name="Spoken languages",
                value=", ".join([m.get("english_name") for m in data["spoken_languages"]]),
            )
        if data.get("genres"):
            embed.add_field(
                name="Genres", value=", ".join([m.get("name") for m in data["genres"]])
            )
        if len(embed.fields) in {5, 8, 11}:
            embed.add_field(name="\u200b", value="\u200b")
        embed.set_footer(
            text="Click arrows to see more info!",
            icon_url="https://i.imgur.com/sSE7Usn.png",
        )
        return embed

    @commands.command(usage="movie name or title")
    @is_apikey_set()
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def movie(self, ctx: commands.Context, *, query: str):
        """Show various info about a movie."""
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")

        async with ctx.channel.typing():
            movie_id = await self.fetch_movie_id(ctx, api_key, query)
            if movie_id == 0: # Cancelled
                return
            if not movie_id:
                return await ctx.send("⛔ No such movie found from given query.")

            data = await self.get(f"{API_BASE}/movie/{movie_id}", {"api_key": api_key})
            if not data:
                return await ctx.send("⛔ Something went wrong when contacting TMDB API.")

            emb1 = self.movie_embed(await ctx.embed_colour(), data)
            emb2 = discord.Embed(colour=await ctx.embed_colour(), title=data.get("title") or "")
            emb2.url = f"https://www.themoviedb.org/movie/{data.get('id', '')}"
            emb2.set_image(url=f"{CDN_BASE}{data.get('backdrop_path', '/')}")
            if data.get("production_companies"):
                emb2.add_field(
                    name="Production Companies",
                    value=", ".join([m.get("name") for m in data["production_companies"]]),
                )
            if data.get("production_countries"):
                emb2.add_field(
                    name="Production Countries",
                    value=", ".join([m.get("name") for m in data["production_countries"]]),
                    inline=False,
                )
            if data.get("tagline"):
                emb2.add_field(name="Tagline", value=data["tagline"], inline=False)

        await menu(ctx, [emb1, emb2], DEFAULT_CONTROLS, timeout=120)

    @commands.command(usage="movie name or title")
    @is_apikey_set()
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def moviecast(self, ctx: commands.Context, *, query: str):
        """Show the given movie's cast (list of actors)."""
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")

        async with ctx.channel.typing():
            movie_id = await self.fetch_movie_id(ctx, api_key, query)
            if movie_id == 0: # Cancelled
                return
            if not movie_id:
                return await ctx.send("⛔ No such movie found from given query.")

            data = await self.get(f"{API_BASE}/movie/{movie_id}/credits", {"api_key": api_key})
            if not data:
                return await ctx.send("⛔ Could not fetch data from TMDB API.")
            if not data.get("cast"):
                return await ctx.send("⛔ No cast or actors data found for this movie.")

            GENDERS_MAP = {"0": "", "1": "♀", "2": "♂"}
            pretty_cast = "\n".join(
                f"**`{i:>2}.`**  [{actor_obj.get('original_name')}]"
                f"(https://www.themoviedb.org/person/{actor_obj.get('id')})"
                f" {GENDERS_MAP[str(actor_obj.get('gender', 0))]}"
                f" as **{actor_obj.get('character')}**"
                for i, actor_obj in enumerate(data["cast"], start=1)
            )

            pages = []
            all_pages = list(pagify(pretty_cast, page_length=1500))
            for i, page in enumerate(all_pages, start=1):
                emb = discord.Embed(colour=discord.Colour.random())
                emb.description = page
                emb.title = f"Movie Cast for {query.title()}"
                emb.url = f"https://www.themoviedb.org/movie/{data.get('id', '')}"
                emb.set_footer(text=f"Page {i} of {len(all_pages)}")
                pages.append(emb)

        controls = {"❌": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=120)

    async def fetch_tv_series_id(
        self, ctx: commands.Context, api_key: str, query: str
    ) -> Optional[int]:
        data = await self.get(f"{API_BASE}/search/tv", {"api_key": api_key, "query": query})
        if not data:
            return None

        if not data.get("results") or len(data.get("results")) == 0:
            return None
        if len(data.get("results")) == 1:
            return data.get("results")[0].get("id")

        # https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
        items = "\n".join(
            f"**{i}.** {v.get('original_name', 'N/A')} "
            + f"({self._parse_date(v.get('first_air_date', ''), 'D')})"
            for i, v in enumerate(data.get("results"), start=1)
        )
        prompt = await ctx.send(
            f"Found multiple results. Please pick one from below:\n\n"
            f"{items.replace('(<t::D>)', '').replace('()', '')}"
        )

        def check(msg: discord.Message) -> bool:
            return bool(
                msg.content.isdigit()
                and int(msg.content) in range(len(items) + 1)
                and msg.author.id == ctx.author.id
                and msg.channel.id == ctx.channel.id
            )

        try:
            choice = await ctx.bot.wait_for("message", timeout=60, check=check)
        except asyncio.TimeoutError:
            choice = None
        if choice is None or choice.content.strip() == "0":
            with suppress(discord.NotFound, discord.HTTPException):
                await prompt.edit(content="No choice was selected. Operation cancelled!")
            return 0

        with suppress(discord.NotFound, discord.HTTPException):
            await prompt.delete()
        return data.get("results")[int(choice.content.strip()) - 1].get("id")

    def tvshow_embed(self, colour: discord.Colour, data: Dict[str, Any]) -> discord.Embed:
        embed = discord.Embed(
            title=data.get("name") or "",
            description=data.get("overview") or "",
            colour=colour,
        )
        embed.url = f"https://www.themoviedb.org/tv/{data.get('id')}"
        # embed.set_image(url=f"{CDN_BASE}{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(url=f"{CDN_BASE}{data.get('poster_path', '/')}")
        if data.get("first_air_date"):
            embed.add_field(name="First Air Date", value=self._parse_date(data["first_air_date"]))
        if data.get("last_air_date"):
            embed.add_field(name="Last Air Date", value=self._parse_date(data["last_air_date"]))
        if data.get("number_of_seasons", 0) > 0:
            embed.add_field(
                name="Seasons",
                value=f"{data['number_of_seasons']} ({data.get('number_of_episodes')} episodes)",
            )
        if data.get("created_by"):
            embed.add_field(
                name="Creators",
                value=", ".join([m.get("name") for m in data.get("created_by")])
            )
        embed.add_field(
            name="Genres",
            value=", ".join([m.get("name") for m in data.get("genres")])
        )
        if data.get("vote_average", 0.0) > 0.0 and data.get("vote_count", 0) > 0:
            embed.add_field(
                name="TMDB Rating",
                value=f"**{data['vote_average']:.1f}** ⭐ / 10\n({data['vote_count']:,} votes)",
            )
        embed.add_field(name="Series status", value=data.get("status", "N/A"))
        embed.add_field(name="Series type", value=data.get("type", "N/A"))
        if data.get("networks"):
            embed.add_field(
                name="Networks", value=", ".join([m.get("name") for m in data["networks"]])
            )
        embed.add_field(
            name="Spoken languages",
            value=", ".join([m.get("english_name") for m in data.get("spoken_languages")]),
        )
        if data.get("seasons"):
            seasons_meta = "\n".join(
                f"**{i}**. {tv.get('name', 'N/A')} ({tv.get('episode_count', 0)} episodes)"
                f" ({self._parse_date(tv['air_date']) if tv.get('air_date') else ''})"
                for i, tv in enumerate(data.get("seasons"), start=1)
            )
            if data.get("episode_run_time"):
                seasons_meta += f"\nAvg. episode runtime: {data['episode_run_time'][0]} minutes"
            embed.add_field(
                name="Seasons summary",
                value=seasons_meta.replace("()", ""),
                inline=False,
            )
        if data.get("next_episode_to_air"):
            next_ep = data["next_episode_to_air"]
            next_airing = "N/A"
            if next_ep.get("air_date"):
                next_airing = self._parse_date(next_ep["air_date"])
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
    async def tvshow(self, ctx: commands.Context, *, query: str):
        """Show various info about a TV show/series."""
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")

        async with ctx.channel.typing():
            tv_series_id = await self.fetch_tv_series_id(ctx, api_key, query)
            if tv_series_id == 0: # Operation cancelled
                return
            if not tv_series_id:
                return await ctx.send("⛔ No such TV show found from given query.")

            data = await self.get(f"{API_BASE}/tv/{tv_series_id}", {"api_key": api_key})
            if not data:
                return await ctx.send("⛔ Could not connect to TMDB API.")

            emb1 = self.tvshow_embed(await ctx.embed_colour(), data)
            emb2 = discord.Embed(colour=await ctx.embed_colour(), title=data.get("name") or "")
            emb2.url = f"https://www.themoviedb.org/tv/{data.get('id')}"
            if data.get("production_countries"):
                emb2.add_field(
                    name="Production Countries",
                    value=", ".join([m.get("name") for m in data["production_countries"]]),
                )
            if data.get("production_companies"):
                emb2.add_field(
                    name="Production Companies",
                    value=", ".join([m.get("name") for m in data["production_companies"]]),
                    inline=False,
                )
            if data.get("tagline"):
                emb2.add_field(name="Tagline", value=data["tagline"], inline=False)

        await menu(ctx, [emb1, emb2], DEFAULT_CONTROLS, timeout=120)

    def suggestmovies_embed(
        self, colour: discord.Colour, footer: str, data: Dict[str, Any]
    ) -> discord.Embed:
        embed = discord.Embed(
            colour=colour,
            title=data.get("title") or "",
            description=data.get("overview") or "",
        )
        embed.url = f"https://www.themoviedb.org/movie/{data.get('id', '')}"
        embed.set_image(url=f"{CDN_BASE}{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(url=f"{CDN_BASE}{data.get('poster_path', '/')}")
        if data.get("release_date"):
            embed.add_field(name="Release Date", value=self._parse_date(data["release_date"]))
        if data.get("vote_average", 0.0) > 0.0 and data.get("vote_count", 0) > 0:
            embed.add_field(
                name="TMDB Rating",
                value=f"**{data['vote_average']:.1f}** ⭐ / 10\n({data['vote_count']:,} votes)",
            )
        embed.set_footer(text=footer, icon_url="https://i.imgur.com/sSE7Usn.png")
        return embed

    @commands.command(aliases=["suggestmovie"], usage="movie name")
    @is_apikey_set()
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def suggestmovies(self, ctx: commands.Context, *, query: str):
        """Get similar movies suggestions based on the given movie title query."""
        async with ctx.channel.typing():
            api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")

            movie_id = await self.fetch_movie_id(ctx, api_key, query)
            if movie_id == 0: # Operation cancelled
                return
            if not movie_id:
                return await ctx.send(f"Movie `{query[:50]}` ... not found.")

            output = await self.get(
                f"{API_BASE}/movie/{movie_id}/recommendations", {"api_key": api_key}
            )
            if not output:
                return await ctx.send("⛔ Could not connect to TMDB API.")
            if not output.get("results"):
                return await ctx.send("No recommendations found related to that movie.")

            pages = []
            for i, data in enumerate(output.get("results"), start=1):
                colour = await ctx.embed_colour()
                footer = f"Page {i} of {len(output['results'])}"
                pages.append(self.suggestmovies_embed(colour, footer, data))

        controls = {"❌": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=120)

    def suggestshows_embed(
        self, colour: discord.Colour, footer: str, data: Dict[str, Any]
    ) -> discord.Embed:
        embed = discord.Embed(
            title=data.get("name") or "",
            description=data.get("overview") or "",
            colour=colour
        )
        embed.url = f"https://www.themoviedb.org/tv/{data.get('id', '')}"
        embed.set_image(url=f"{CDN_BASE}{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(url=f"{CDN_BASE}{data.get('poster_path', '/')}")
        if data.get("first_air_date"):
            embed.add_field(name="First Air Date", value=self._parse_date(data["first_air_date"]))
        if data.get("vote_average", 0.0) > 0.0 and data.get("vote_count", 0) > 0:
            embed.add_field(
                name="TMDB Rating",
                value=f"**{data['vote_average']:.1f}** ⭐ / 10 ({data['vote_count']:,} votes)",
            )
        embed.set_footer(text=footer, icon_url="https://i.imgur.com/sSE7Usn.png")
        return embed

    @commands.command(aliases=["suggestseries", "suggestshow"], usage="tv series name/title")
    @is_apikey_set()
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def suggestshows(self, ctx: commands.Context, *, query: str):
        """Get similar TV show suggestions from the given TV series title query."""
        async with ctx.channel.typing():
            api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")

            tv_series_id = await self.fetch_tv_series_id(ctx, api_key, query)
            if tv_series_id == 0: # Operation cancelled
                return
            if tv_series_id is None:
                return await ctx.send(f"TV show `{query[:50]}` ... not found.")

            output = await self.get(
                f"{API_BASE}/tv/{tv_series_id}/recommendations", {"api_key": api_key}
            )
            if not output:
                return await ctx.send("⛔ Could not connect to TMDB API.")
            if not output.get("results"):
                return await ctx.send("No recommendations found related to that TV show.")

            pages = []
            for i, data in enumerate(output["results"], start=1):
                colour = await ctx.embed_colour()
                footer = f"Page {i} of {len(output['results'])}"
                pages.append(self.suggestshows_embed(colour, footer, data))

        controls = {"❌": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=120)
