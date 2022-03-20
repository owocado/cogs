import asyncio
from datetime import datetime
from typing import List, Optional, Union

import aiohttp
import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.menus import DEFAULT_CONTROLS, close_menu, menu
# from redbot.core.utils.dpy2_menus import BaseMenu, ListPages

PageType = List[Union[discord.Embed, str]]


class MovieDB(commands.Cog):
    """Get some info about a movie or TV show/series."""

    __author__, __version__ = ("Author: ow0x", "Cog Version: 1.0.2")

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        # this cog does not store any end user data YET
        # TODO: change this when watchlist/todolist is added
        pass

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\n{self.__author__}\n{self.__version__}"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self) -> None:
        asyncio.create_task(self.session.close())

    def tstamp(self, date_string: str, style: str = "R") -> str:
        try:
            timestamp = datetime.strptime(date_string, "%Y-%m-%d").timestamp()
            return f"<t:{int(timestamp)}:{style}>"
        # Future proof it in case API changes date string
        except ValueError:
            return "unknown"

    async def get(self, url: str, params: dict):
        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
        except asyncio.TimeoutError:
            return None

    async def fetch_movie_id(self, ctx: commands.Context, query: str) -> Optional[int]:
        url = "https://api.themoviedb.org/3/search/movie"
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        data = await self.get(url, {"api_key": api_key, "query": query})
        if data is None:
            return None

        if not data.get("results") or len(data.get("results")) == 0:
            return None
        elif len(data.get("results")) == 1:
            return data.get("results")[0].get("id")
        else:
            # Logic taken/modified from https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
            items = "\n".join(
                f"**{i}.** {v.get('title', 'N/A')} ({self.tstamp(v.get('release_date', ''), 'D')})"
                for i, v in enumerate(data["results"], 1)
            )
            choices = "Found multiple results. Please select one from below:\n\n"
            send_to_channel = await ctx.send(f"{choices}{items.replace('(<t::D>)', '')}")

            def check(msg) -> bool:
                return bool(
                    msg.content.isdigit()
                    and int(msg.content) in range(len(items) + 1)
                    and msg.author.id == ctx.author.id
                    and msg.channel.id == ctx.channel.id
                )

            try:
                choice = await self.bot.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                choice = None
            if choice is None or choice.content.strip() == "0":
                await send_to_channel.edit(content="Operation cancelled.")
                return None
            else:
                await send_to_channel.delete()
                return data["results"][int(choice.content.strip()) - 1].get("id")

    def movie_embed(self, meta, data) -> discord.Embed:
        embed = discord.Embed(
            title=data.get("title", ""),
            description=data.get("overview", ""),
            colour=meta,
        )
        if data.get("imdb_id"):
            embed.url = f"https://www.imdb.com/title/{data['imdb_id']}"
        embed.set_image(url=f"https://image.tmdb.org/t/p/original{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(
            url=f"https://image.tmdb.org/t/p/original{data.get('poster_path', '/')}"
        )
        if data.get("release_date"):
            embed.add_field(name="Release Date", value=self.tstamp(data["release_date"]))
        if data.get("runtime", 0) > 0:
            hours, minutes = (data.get("runtime", 0) // 60, data.get("runtime", 0) % 60)
            embed.add_field(name="Runtime", value=f"{hours}h {minutes}m")
        if data.get("budget", 0) > 0:
            embed.add_field(name="Budget", value=f'${data.get("budget", 0):,}')
        if data.get("revenue", 0) > 0:
            embed.add_field(name="Revenue", value=f'${data.get("revenue", 0):,}')
        if data.get("vote_average", 0.0) > 0.0 and data.get("vote_count", 0) > 0:
            rating = f"{round(data['vote_average'], 1)} / 10\n({data['vote_count']:,} votes)"
            embed.add_field(name="TMDB Rating", value=rating)
        if data.get("spoken_languages"):
            spoken_languages = "\n".join([m.get("english_name") for m in data["spoken_languages"]])
            embed.add_field(name="Spoken languages", value=spoken_languages)
        if data.get("genres"):
            embed.add_field(
                name="Genres", value="\n".join([m.get("name") for m in data["genres"]])
            )
        if data.get("production_companies"):
            production_companies = "\n".join([m.get("name") for m in data["production_companies"]])
            embed.add_field(name="Production compananies", value=production_companies)
        if len(embed.fields) in [5, 8, 11]:
            embed.add_field(name="\u200b", value="\u200b")
        if data.get("production_countries"):
            production_countries = ", ".join([m.get("name") for m in data["production_countries"]])
            embed.add_field(name="Production countries", value=production_countries, inline=False)
        if data.get("tagline"):
            embed.add_field(name="Tagline", value=data.get("tagline"))
        embed.set_footer(
            text="Powered by themoviedb API ❤️",
            icon_url="https://i.imgur.com/sSE7Usn.png",
        )
        return embed

    @commands.command(usage="movie name or title")
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def movie(self, ctx: commands.Context, *, query: str):
        """Show various info about a movie."""
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        if not api_key:
            return await ctx.send("Bot owner need to set an API key first!")

        await ctx.trigger_typing()
        movie_id = await self.fetch_movie_id(ctx, query)
        if movie_id is None:
            return await ctx.send("Could not find any results.")

        base_url, params = (f"https://api.themoviedb.org/3/movie/{movie_id}", {"api_key": api_key})
        data = await self.get(base_url, params)
        if not data:
            return await ctx.send("Something went wrong when contacting TMDB API.")
        embed = self.movie_embed(await ctx.embed_colour(), data)
        await ctx.send(embed=embed)

    async def fetch_tv_series_id(self, ctx: commands.Context, query: str) -> Optional[int]:
        url = "http://api.themoviedb.org/3/search/tv"
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        params = {"api_key": api_key, "query": query}
        data = await self.get(url, params)
        if data is None:
            return None

        if not data.get("results") or len(data.get("results")) == 0:
            return None
        elif len(data.get("results")) == 1:
            return data.get("results")[0].get("id")
        else:
            # https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
            items = "\n".join(
                f"**{i}.** {v.get('original_name', 'N/A')} ({self.tstamp(v.get('first_air_date', ''), 'D')})"
                for i, v in enumerate(data.get("results"), start=1)
            )
            choices = "Found multiple results. Please select one from below:\n\n"
            send_to_channel = await ctx.send(f"{choices}{items.replace('(<t::D>)', '')}")

            def check(msg) -> bool:
                return bool(
                    msg.content.isdigit()
                    and int(msg.content) in range(len(items) + 1)
                    and msg.author.id == ctx.author.id
                    and msg.channel.id == ctx.channel.id
                )

            try:
                choice = await self.bot.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                choice = None
            if choice is None or choice.content.strip() == "0":
                await send_to_channel.edit(content="Operation cancelled.")
                return None
            else:
                await send_to_channel.delete()
                return data.get("results")[int(choice.content.strip()) - 1].get("id")

    def tvshow_embed(self, meta, data) -> discord.Embed:
        embed = discord.Embed(
            title=data.get("name", ""), description=data.get("overview", ""), colour=meta
        )
        if data.get("homepage"):
            embed.url = data["homepage"]
        embed.set_image(url=f"https://image.tmdb.org/t/p/original{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(
            url=f"https://image.tmdb.org/t/p/original{data.get('poster_path', '/')}"
        )
        if data.get("first_air_date"):
            embed.add_field(name="First Air Date", value=self.tstamp(data["first_air_date"]))
        if data.get("last_air_date"):
            embed.add_field(name="Last Air Date", value=self.tstamp(data["last_air_date"]))
        if data.get("number_of_seasons", 0) > 0:
            embed.add_field(
                name="Seasons",
                value=f"{data.get('number_of_seasons')} ({data.get('number_of_episodes')} episodes)",
            )
        if data.get("created_by"):
            creators = ", ".join(m.get("name") for m in data.get("created_by"))
            embed.add_field(name="Creators", value=creators)
        embed.add_field(
            name="Genres", value=", ".join([m.get("name") for m in data.get("genres")])
        )
        if data.get("vote_average", 0.0) > 0.0 and data.get("vote_count", 0) > 0:
            rating = f"{round(data['vote_average'], 1)} / 10\n({data['vote_count']:,} votes)"
            embed.add_field(name="TMDB Rating", value=rating)
        embed.add_field(name="Series status", value=data.get("status", "N/A"))
        embed.add_field(name="Series type", value=data.get("type", "N/A"))
        embed.add_field(
            name="Networks", value=", ".join([m.get("name") for m in data.get("networks")])
        )
        spoken_languages = "\n".join([m.get("english_name") for m in data.get("spoken_languages")])
        embed.add_field(name="Spoken languages", value=spoken_languages)
        if data.get("production_countries"):
            production_countries = ", ".join([m.get("name") for m in data["production_countries"]])
            embed.add_field(name="Production countries", value=production_countries)
        if data.get("production_companies"):
            production_companies = ", ".join([m.get("name") for m in data["production_companies"]])
            embed.add_field(
                name="Production compananies", value=production_companies, inline=False
            )
        avg_episode_runtime = f"Average episode runtime: {data.get('episode_run_time')[0]} minutes"
        seasons_meta = "\n".join(
            f"**{i}**. {tv.get('name', 'N/A')} ({tv.get('episode_count', 0)} episodes) "
            f"({self.tstamp(tv['air_date']) if tv.get('air_date') else ''})"
            for i, tv in enumerate(data.get("seasons"), start=1)
        )
        embed.add_field(
            name="Seasons summary",
            value=f"{seasons_meta.replace('()', '')}\n{avg_episode_runtime}",
            inline=False,
        )
        if data.get("next_episode_to_air"):
            next_ep = data["next_episode_to_air"]
            next_airing = "N/A"
            if next_ep.get("air_date"):
                next_airing = self.tstamp(next_ep["air_date"])
            next_episode_info = (
                f"**S{next_ep.get('season_number', 0)}E{next_ep.get('episode_number', 0)}: "
                f"{next_ep.get('name', 'N/A')}**\n`next airing:` {next_airing}"
            )
            embed.add_field(name="Info on next episode", value=next_episode_info, inline=False)
        if data.get("tagline"):
            embed.add_field(name="Tagline", value=data.get("tagline"))
        in_production = "In production? " + ("Yes" if data.get("in_production") else "No")
        embed.set_footer(
            text=f"{in_production} • Powered by themoviedb API ❤️",
            icon_url="https://i.imgur.com/sSE7Usn.png",
        )
        return embed

    @commands.command(usage="tvshow name or title")
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def tvshow(self, ctx: commands.Context, *, query: str):
        """Show various info about a TV show/series."""
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        if not api_key:
            return await ctx.send("Bot owner need to set an API key first!")

        await ctx.trigger_typing()
        tv_series_id = await self.fetch_tv_series_id(ctx, query)
        if tv_series_id is None:
            return await ctx.send("Could not find any results.")

        url, params = (f"https://api.themoviedb.org/3/tv/{tv_series_id}", {"api_key": api_key})
        data = await self.get(url, params)
        if not data:
            return await ctx.send("Could not connect to TMDB API.")
        embed = self.tvshow_embed(await ctx.embed_colour(), data)
        await ctx.send(embed=embed)

    def suggestmovies_embed(self, colour, footer, data) -> discord.Embed:
        embed = discord.Embed(
            colour=colour, title=data.get("title", ""), description=data.get("overview", "")
        )
        embed.url = f"https://www.themoviedb.org/movie/{data.get('id', '')}"
        embed.set_image(url=f"https://image.tmdb.org/t/p/original{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(
            url=f"https://image.tmdb.org/t/p/original{data.get('poster_path', '/')}"
        )
        if data.get("release_date"):
            embed.add_field(name="Release Date", value=self.tstamp(data["release_date"]))
        if data.get("vote_average", 0.0) > 0.0 and data.get("vote_count", 0) > 0:
            rating = f"{round(data['vote_average'], 1)} / 10 ({data['vote_count']:,} votes)"
            embed.add_field(name="TMDB Rating", value=rating)
        embed.set_footer(text=footer, icon_url="https://i.imgur.com/sSE7Usn.png")
        return embed

    @commands.command(usage="movie name")
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def suggestmovies(self, ctx: commands.Context, *, query: str):
        """Get similar movies suggestions based on a movie title."""
        await ctx.trigger_typing()
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        if not api_key:
            return await ctx.send("Bot owner need to set an API key first!")
        movie_id = await self.fetch_movie_id(ctx, query)
        if movie_id is None:
            return await ctx.send(f"Movie `{query[:50]}` ... not found.")

        url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations"
        output = await self.get(url, {"api_key": api_key})
        if not output:
            return await ctx.send("Could not connect to TMDB API.")
        if not output.get("results"):
            return await ctx.send("No recommendations found for that movie. 🤔")
        pages: PageType = []
        for i, data in enumerate(output.get("results"), start=1):
            colour = await ctx.embed_colour()
            footer = f"Page {i} of {len(output['results'])} • Powered by themoviedb API ❤️"
            embed = self.suggestmovies_embed(colour, footer, data)
            pages.append(embed)

        controls = {"": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=90.0)
        # await BaseMenu(ListPages(pages), ctx=ctx).start(ctx)

    def suggestshows_embed(self, colour, footer, data) -> discord.Embed:
        embed = discord.Embed(
            title=data.get("name", ""), description=data.get("overview", ""), colour=colour
        )
        embed.url = f"https://www.themoviedb.org/tv/{data.get('id', '')}"
        embed.set_image(url=f"https://image.tmdb.org/t/p/original{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(
            url=f"https://image.tmdb.org/t/p/original{data.get('poster_path', '/')}"
        )
        if data.get("first_air_date"):
            embed.add_field(name="First Air Date", value=self.tstamp(data["first_air_date"]))
        if data.get("vote_average", 0.0) > 0.0 and data.get("vote_count", 0) > 0:
            rating = f"{round(data['vote_average'], 1)} / 10 ({data['vote_count']:,} votes)"
            embed.add_field(name="TMDB Rating", value=rating)
        embed.set_footer(text=footer, icon_url="https://i.imgur.com/sSE7Usn.png")
        return embed

    @commands.command(usage="tv series name/title")
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def suggestshows(self, ctx: commands.Context, *, query: str):
        """Get similar TV show suggestions from a TV series title."""
        await ctx.trigger_typing()
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        if not api_key:
            return await ctx.send("Bot owner need to set an API key first!")
        tv_series_id = await self.fetch_tv_series_id(ctx, query)
        if tv_series_id is None:
            return await ctx.send(f"TV show `{query[:50]}` ... not found.")

        base_url = f"https://api.themoviedb.org/3/tv/{tv_series_id}/recommendations"
        output = await self.get(base_url, {"api_key": api_key})
        if not output:
            return await ctx.send("Could not connect to TMDB API.")
        if not output.get("results"):
            return await ctx.send("No recommendations found for that movie. 🤔")
        pages: PageType = []
        for i, data in enumerate(output.get("results"), start=1):
            colour = await ctx.embed_colour()
            footer = f"Page {i} of {len(output['results'])} • Powered by themoviedb API ❤️"
            embed = self.suggestshows_embed(colour, footer, data)
            pages.append(embed)

        controls = {"": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=90.0)
        # await BaseMenu(ListPages(pages), ctx=ctx).start(ctx)
