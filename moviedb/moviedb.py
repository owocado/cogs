import asyncio
from datetime import datetime

import aiohttp
import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_number as hnum
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
# from redbot.core.utils.xmenus import BaseMenu, ListPages


class MovieDB(commands.Cog):
    """Show various info about a movie or a TV show/series."""

    __author__ = "ow0x"
    __version__ = "0.2.3"
    
    async def red_delete_data_for_user(self, **kwargs):
        """ Nothing to delete """
        # this cog does not store any end user data YET
        # TODO: change this when watchlist/todolist is added
        pass

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot: Red):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    def get_timestamp(self, date_string: str, style: str = "R") -> str:
        try:
            timestamp = datetime.strptime(date_string, "%Y-%m-%d").timestamp()
            return f"<t:{int(timestamp)}:{style}>"
        # Future proof it in case API changes date string
        except ValueError:
            return "unknown"

    async def fetch_movie_id(self, ctx: commands.Context, query: str):
        url = "https://api.themoviedb.org/3/search/movie"
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        params = {"api_key": api_key, "query": query}
        try:
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                data = await response.json()
        except asyncio.TimeoutError:
            return None

        if len(data.get("results")) == 0:
            return None
        elif len(data.get("results")) == 1:
            movie_id = data.get("results")[0].get("id")
            return movie_id
        elif len(data.get("results")) > 1:
            # This logic taken from https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
            # All credits belong to Sitryk, I do not take any credit for this code snippet.
            items = ""
            for i, obj in enumerate(data.get("results"), start=1):
                items += "**{}.** {}{}\n".format(
                    i,
                    obj.get("title", "Missing title"),
                    f" ({self.get_timestamp(obj['release_date'], 'D')})"
                    if obj.get("release_date") and obj["release_date"] != "" else "",
                )
            choices = f"Found multiple results. Please select one from below:\n\n{items}"
            send_to_channel = await ctx.send(choices)

            def check(msg):
                content = msg.content
                if (
                    content.isdigit()
                    and int(content) in range(0, len(items) + 1)
                    and msg.author is ctx.author
                    and msg.channel is ctx.channel
                ):
                    return True

            try:
                choice = await self.bot.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                choice = None

            if choice is None or choice.content.strip() == "0":
                await send_to_channel.edit(content="Operation cancelled.")
                return None
            else:
                choice = choice.content.strip()
                choice = int(choice) - 1
                movie_id = data.get("results")[choice].get("id")
                await send_to_channel.delete()
                return movie_id
        else:
            return None

    @commands.command(usage="<movie_name_or_title>")
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def movie(self, ctx: commands.Context, *, query: str):
        """Show various info about a movie."""
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        if not api_key:
            return await ctx.send("Please set an API key first!")

        await ctx.trigger_typing()
        movie_id = await self.fetch_movie_id(ctx, query)
        if movie_id is None:
            return await ctx.send("Could not find any results.")

        base_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        params = {"api_key": api_key}
        try:
            async with self.session.get(base_url, params=params) as response:
                if response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                data = await response.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        embed = discord.Embed(
            title=str(data["title"]),
            description=data.get("overview", "No summary."),
            colour=await ctx.embed_color(),
        )
        if data.get("imdb_id"):
            embed.url = f"https://www.imdb.com/title/{data['imdb_id']}"
        embed.set_image(url=f"https://image.tmdb.org/t/p/original{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/original{data.get('poster_path', '/')}")
        if data.get("release_date", "") != "":
            embed.add_field(
                name="Release Date",
                value=self.get_timestamp(data["release_date"]),
            )
        if data.get("runtime") > 0:
            hours = data.get("runtime", 0) // 60
            mins = data.get("runtime", 0) % 60
            embed.add_field(name="Runtime", value=f"{hours}h {mins}m")
        if data.get("budget") > 0:
            embed.add_field(name="Budget", value="$" + hnum(data.get("budget")))
        if data.get("revenue") > 0:
            embed.add_field(name="Revenue", value="$" + hnum(data.get("revenue")))
        if data.get("vote_average", 0.0) > 0.0 and data.get("vote_count", 0) > 0:
            rating = f"{round(data['vote_average'], 1)} / 10\n({hnum(data['vote_count'])} votes)"
            embed.add_field(name="TMDB Rating", value=rating)
        if data.get("genres"):
            genres = ", ".join([m.get("name") for m in data["genres"]])
            embed.add_field(name="Genres", value=genres)
        if len(embed.fields) == 5:
            embed.add_field(name="\u200b", value="\u200b")
        if data.get("spoken_languages"):
            spoken_languages = ", ".join([m.get("english_name") for m in data["spoken_languages"]])
            embed.add_field(name="Spoken languages", value=spoken_languages, inline=False)
        if data.get("production_companies"):
            production_companies = ", ".join([m.get("name") for m in data["production_companies"]])
            embed.add_field(name="Production compananies", value=production_companies, inline=False)
        if data.get("production_countries"):
            production_countries = ", ".join([m.get("name") for m in data["production_countries"]])
            embed.add_field(name="Production countries", value=production_countries, inline=False)
        if data.get("tagline", "") != "":
            embed.add_field(name="Tagline", value=data.get("tagline"))
        embed.set_footer(
            text="Powered by themoviedb API ❤️",
            icon_url="https://i.imgur.com/sSE7Usn.png",
        )

        await ctx.send(embed=embed)

    async def fetch_tv_series_id(self, ctx: commands.Context, query: str):
        url = "http://api.themoviedb.org/3/search/tv"
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        params = {"api_key": api_key, "query": query}
        try:
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                data = await response.json()
        except asyncio.TimeoutError:
            return None

        if len(data.get("results")) == 0:
            return None
        elif len(data.get("results")) == 1:
            tv_series_id = data.get("results")[0].get("id")
            return tv_series_id
        elif len(data.get("results")) > 1:
            # This logic taken from https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
            # All credits belong to Sitryk, I do not take any credit for this code snippet.
            items = ""
            for i, obj in enumerate(data.get("results"), start=1):
                items += "**{}.** {}{}\n".format(
                    i,
                    obj.get("original_name", "Missing title"),
                    f" ({self.get_timestamp(obj['first_air_date'], 'D')})"
                    if obj.get("first_air_date") and obj["first_air_date"] != "" else "",
                )
            choices = f"Found multiple results. Please select one from below:\n\n{items}"
            send_to_channel = await ctx.send(choices)

            def check(msg):
                content = msg.content
                if (
                    content.isdigit()
                    and int(content) in range(0, len(items) + 1)
                    and msg.author is ctx.author
                    and msg.channel is ctx.channel
                ):
                    return True

            try:
                choice = await self.bot.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                choice = None

            if choice is None or choice.content.strip() == "0":
                await send_to_channel.edit(content="Operation cancelled.")
                return None
            else:
                choice = choice.content.strip()
                choice = int(choice) - 1
                tv_series_id = data.get("results")[choice].get("id")
                await send_to_channel.delete()
                return tv_series_id
        else:
            return None

    @commands.command(usage="<tvshow_name_or_title>")
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def tvshow(self, ctx: commands.Context, *, query: str):
        """Show various info about a TV show/series."""
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        if not api_key:
            return await ctx.send("Please set an API key first!")

        await ctx.trigger_typing()
        tv_series_id = await self.fetch_tv_series_id(ctx, query)
        if tv_series_id is None:
            return await ctx.send("Could not find any results.")

        base_url = f"https://api.themoviedb.org/3/tv/{tv_series_id}"
        params = {"api_key": api_key}
        try:
            async with self.session.get(base_url, params=params) as response:
                if response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                data = await response.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        embed = discord.Embed(
            title=str(data["name"]),
            description=data.get("overview", "No summary."),
            colour=await ctx.embed_color(),
        )
        if data.get("homepage"):
            embed.url = data["homepage"]
        embed.set_image(url=f"https://image.tmdb.org/t/p/original{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/original{data.get('poster_path', '/')}")
        if data.get("first_air_date", "") != "":
            embed.add_field(
                name="First Air Date",
                value=self.get_timestamp(data["first_air_date"]),
            )
        if data.get("last_air_date", "") != "":
            embed.add_field(
                name="Last Air Date",
                value=self.get_timestamp(data["last_air_date"]),
            )
        if data.get("number_of_seasons", 0) > 0:
            embed.add_field(
                name="Seasons",
                value=f"{data.get('number_of_seasons')} ({data.get('number_of_episodes')} episodes)",
            )
        if data.get("created_by"):
            creators = ", ".join(m.get("name") for m in data.get("created_by"))
            embed.add_field(name="Creators", value=creators)
        genres = ", ".join([m.get("name") for m in data.get("genres")])
        embed.add_field(name="Genres", value=genres)
        if data.get("vote_average", 0.0) > 0.0 and data.get("vote_count", 0) > 0:
            rating = (
                f"{round(data['vote_average'], 1)} / 10\n({hnum(data.get('vote_count'))} votes)"
            )
            embed.add_field(name="TMDB Rating", value=rating)
        embed.add_field(name="In production?", value="Yes" if data.get("in_production") else "No")
        embed.add_field(name="Series status", value=data.get("status", "N/A"))
        embed.add_field(name="Series type", value=data.get("type", "N/A"))
        networks = ", ".join([m.get("name") for m in data.get("networks")])
        embed.add_field(name="Networks", value=networks, inline=False)
        spoken_languages = ", ".join([m.get("english_name") for m in data.get("spoken_languages")])
        embed.add_field(name="Spoken languages", value=spoken_languages, inline=False)
        if data.get("production_companies"):
            production_companies = ", ".join([m.get("name") for m in data["production_companies"]])
            embed.add_field(name="Production compananies", value=production_companies, inline=False)
        if data.get("production_countries"):
            production_countries = ", ".join(
                [m.get("name") for m in data["production_countries"]]
            )
            embed.add_field(name="Production countries", value=production_countries, inline=False)
        avg_episode_runtime = f"Average episode runtime: {data.get('episode_run_time')[0]} minutes"
        seasons_meta = ""
        for i, obj in enumerate(data.get("seasons"), start=1):
            seasons_meta += "**{}**. {} ({} episodes){}\n".format(
                i,
                obj.get("name", "N/A"),
                obj.get("episode_count", 0),
                f" ({self.get_timestamp(obj['air_date'])})"
                if obj.get("air_date") and obj['air_date'] != "" else "",
            )
        embed.add_field(
            name="Seasons summary",
            value=f"{seasons_meta}\n{avg_episode_runtime}",
            inline=False,
        )
        if data.get("next_episode_to_air"):
            next_ep = data["next_episode_to_air"]
            next_airing = "N/A"
            if next_ep.get("air_date"):
                next_airing = self.get_timestamp(next_ep['air_date'])
            next_episode_info = (
                f"**S{next_ep.get('season_number', 0)}E{next_ep.get('episode_number', 0)}: "
                f"{next_ep.get('name', 'N/A')}**\n`next airing:` {next_airing}"
            )
            embed.add_field(name="Info on next episode", value=next_episode_info, inline=False)
        if data.get("tagline", "") != "":
            embed.add_field(name="Tagline", value=data.get("tagline"))
        embed.set_footer(
            text="Powered by themoviedb API ❤️",
            icon_url="https://i.imgur.com/sSE7Usn.png",
        )

        await ctx.send(embed=embed)

    @commands.command(usage="<movie_name>")
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def suggestmovies(self, ctx: commands.Context, *, query: str):
        """Get movies suggestions based on a movie title."""
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        if not api_key:
            return await ctx.send("Please set an API key first!")

        await ctx.trigger_typing()
        movie_id = await self.fetch_movie_id(ctx, query)
        if movie_id is None:
            return await ctx.send(f"Movie `{query[:50]}` ... not found.")

        base_url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations"
        params = {"api_key": api_key}
        try:
            async with self.session.get(base_url, params=params) as response:
                if response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                output = await response.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        if not output.get("results"):
            return await ctx.send("No recommendations found for that movie. 🤔")

        pages = []
        for i, data in enumerate(output.get("results"), start=1):
            embed = discord.Embed(colour=await ctx.embed_color())
            embed.title = str(data["title"])
            embed.description = data.get("overview", "No summary.")
            embed.url = f"https://www.themoviedb.org/movie/{data.get('id', '')}"
            embed.set_image(url=f"https://image.tmdb.org/t/p/original{data.get('backdrop_path', '/')}")
            embed.set_thumbnail(
                url=f"https://image.tmdb.org/t/p/original{data.get('poster_path', '/')}"
            )
            if data.get("release_date", "") != "":
                embed.add_field(
                    name="Release Date",
                    value=self.get_timestamp(data["release_date"]),
                )
            if data.get("vote_average", 0.0) > 0.0 and data.get("vote_count", 0) > 0:
                rating = f"{round(data['vote_average'], 1)} / 10\n({hnum(data['vote_count'])} votes)"
                embed.add_field(name="TMDB Rating", value=rating)
            embed.set_footer(
                text=f"Page {i} of {len(output['results'])} • Powered by themoviedb API ❤️",
                icon_url="https://i.imgur.com/sSE7Usn.png",
            )
            pages.append(embed)

        if len(pages) == 1:
            return await ctx.send(embed=pages[0])
        else:
            await menu(ctx, pages, DEFAULT_CONTROLS, timeout=60.0)
            # await BaseMenu(ListPages(pages), ctx=ctx).start(ctx)

    @commands.command(usage="<tv_series_name_or_title>")
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def suggestshows(self, ctx: commands.Context, *, query: str):
        """Get TV show suggestions related to a TV series title."""
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        if not api_key:
            return await ctx.send("Please set an API key first!")

        await ctx.trigger_typing()
        tv_series_id = await self.fetch_tv_series_id(ctx, query)
        if tv_series_id is None:
            return await ctx.send(f"TV show `{query[:50]}` ... not found.")

        base_url = f"https://api.themoviedb.org/3/tv/{tv_series_id}/recommendations"
        params = {"api_key": api_key}
        try:
            async with self.session.get(base_url, params=params) as response:
                if response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                output = await response.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        if not output.get("results"):
            return await ctx.send("No recommendations found for this TV show. 🤔")

        pages = []
        for i, data in enumerate(output.get("results"), start=1):
            embed = discord.Embed(
                title=str(data["name"]),
                description=data.get("overview", "No summary."),
                colour=await ctx.embed_color(),
            )
            embed.url = f"https://www.themoviedb.org/tv/{data.get('id', '')}"
            embed.set_image(url=f"https://image.tmdb.org/t/p/original{data.get('backdrop_path', '/')}")
            embed.set_thumbnail(
                url=f"https://image.tmdb.org/t/p/original{data.get('poster_path', '/')}"
            )
            if data.get("first_air_date", "") != "":
                embed.add_field(
                    name="First Air Date",
                    value=self.get_timestamp(data["first_air_date"]),
                )
            if data.get("vote_average", 0.0) > 0.0 and data.get("vote_count", 0) > 0:
                rating = f"{round(data['vote_average'], 1)} / 10\n({hnum(data['vote_count'])} votes)"
                embed.add_field(name="TMDB Rating", value=rating)
            embed.set_footer(
                text=f"Page {i} of {len(output['results'])} | Powered by themoviedb API ❤️",
                icon_url="https://i.imgur.com/sSE7Usn.png",
            )
            pages.append(embed)

        if len(pages) == 1:
            return await ctx.send(embed=pages[0])
        else:
            await menu(ctx, pages, DEFAULT_CONTROLS, timeout=60.0)
            # await BaseMenu(ListPages(pages), ctx=ctx).start(ctx)
