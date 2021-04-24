import aiohttp
import asyncio

# Required by Red
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import bold, humanize_number, pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

# Taken from https://github.com/flaree/Flare-Cogs/blob/master/dankmemer/dankmemer.py#L16
# Many thanks to flare <3
async def tokencheck(ctx):
    token = await ctx.bot.get_shared_api_tokens("tmdb")
    return bool(token.get("api_key"))


class MovieDB(commands.Cog):
    """Show various info about a movie or a TV show/series."""

    __author__ = ["siu3334 (<@306810730055729152>)"]
    __version__ = "0.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

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
            for count, value in enumerate(data.get("results")):
                items += "**{}.** {} ({})\n".format(
                    count + 1,
                    value.get("title", "Missing title"),
                    value.get("release_date", "Not released yet"),
                )
            choices = f"Found multiple results for your movie query. Please select one from below:\n\n{items}"
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

    @commands.command()
    @commands.check(tokencheck)
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def movie(self, ctx: commands.Context, *, query: str):
        """Show various info about a movie."""
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")

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
            title=data.get("title", "Untitled movie"),
            description=data.get("overview", "No summary."),
            colour=await ctx.embed_color(),
        )
        embed.url = f"https://www.imdb.com/title/{data.get('imdb_id', '')}"
        # embed.set_image(url=f"https://image.tmdb.org/t/p/w500{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{data.get('poster_path', '/')}")
        if data.get("release_date") != "":
            embed.add_field(
                name="Release Date (USA)",
                value=data.get("release_date", "Not released yet."),
            )
        if data.get("runtime") > 0:
            hours = data.get("runtime", 0) // 60
            mins = data.get("runtime", 0) % 60
            embed.add_field(name="Runtime", value=f"{hours}h {mins}m")
        if data.get("budget") > 0:
            embed.add_field(name="Budget", value="$" + humanize_number(data.get("budget")))
        if data.get("revenue") > 0:
            embed.add_field(name="Revenue", value="$" + humanize_number(data.get("revenue")))
        if data.get("vote_average") > 0.0 and data.get("vote_count") > 0:
            rating = f"{round(data.get('vote_average') * 10)}% ({humanize_number(data.get('vote_count'))} votes)"
            embed.add_field(name="TMDB Rating", value=rating)
        genres = "\n".join([m.get("name") for m in data.get("genres")])
        embed.add_field(name="Genres", value=genres)
        spoken_languages = ", ".join(
            [m.get("english_name") for m in data.get("spoken_languages")]
        )
        embed.add_field(name="Spoken languages", value=spoken_languages, inline=False)
        production_companies = "\n".join(
            [m.get("name") for m in data.get("production_companies")]
        )
        embed.add_field(
            name="Production compananies", value=production_companies, inline=False
        )
        production_countries = "\n".join(
            [m.get("name") for m in data.get("production_countries")]
        )
        embed.add_field(
            name="Production countries", value=production_countries, inline=False
        )
        if data.get("tagline", "") != "":
            embed.add_field(name="Tagline", value=data.get("tagline"))
        embed.set_footer(
            text="Information provided by themoviedb API ❤️",
            icon_url="https://i.imgur.com/3K3QMv9.png",
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
            for count, value in enumerate(data.get("results")):
                items += "**{}.** {} ({})\n".format(
                    count + 1,
                    value.get("original_name", "Missing title"),
                    value.get("first_air_date", "Not released yet"),
                )
            choices = f"Found multiple results for your TV Show query. Please select one from below:\n\n{items}"
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

    @commands.command(aliases=["tv"])
    @commands.check(tokencheck)
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def tvshow(self, ctx: commands.Context, *, query: str):
        """Show various info about a movie."""
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")

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
            title=data.get("name", "Untitled movie"),
            description=data.get("overview", "No summary."),
            colour=await ctx.embed_color(),
        )
        embed.url = f"https://www.imdb.com/title/{data.get('imdb_id', '')}"
        # embed.set_image(url=f"https://image.tmdb.org/t/p/w500{data.get('backdrop_path', '/')}")
        embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{data.get('poster_path', '/')}")
        if data.get("first_air_date") != "":
            embed.add_field(
                name="First Air Date",
                value=data.get("first_air_date", "Not released yet."),
            )
        if data.get("last_air_date") != "":
            embed.add_field(
                name="Last Air Date",
                value=data.get("last_air_date", "Not released yet."),
            )
        if data.get("number_of_seasons", 0) > 0:
            embed.add_field(
                name="Seasons",
                value=f"{data.get('number_of_seasons')} ({data.get('number_of_episodes')} episodes)",
            )
        creators = ", ".join([m.get("name") for m in data.get("created_by")])
        embed.add_field(name="Creators", value=creators)
        genres = "\n".join([m.get("name") for m in data.get("genres")])
        embed.add_field(name="Genres", value=genres)
        if data.get("vote_average") > 0.0 and data.get("vote_count") > 0:
            rating = f"{round(data.get('vote_average') * 10)}% ({humanize_number(data.get('vote_count'))} votes)"
            embed.add_field(name="TMDB Rating", value=rating)
        embed.add_field(
            name="In production?", value="Yes" if data.get("in_production") else "No"
        )
        embed.add_field(name="Series status", value=data.get("status", "N/A"))
        embed.add_field(name="Series type", value=data.get("type", "N/A"))
        networks = ", ".join([m.get("name") for m in data.get("networks")])
        embed.add_field(name="Networks", value=networks, inline=False)
        spoken_languages = ", ".join(
            [m.get("english_name") for m in data.get("spoken_languages")]
        )
        embed.add_field(name="Spoken languages", value=spoken_languages, inline=False)
        production_companies = "\n".join(
            [m.get("name") for m in data.get("production_companies")]
        )
        embed.add_field(
            name="Production compananies", value=production_companies, inline=False
        )
        production_countries = "\n".join(
            [m.get("name") for m in data.get("production_countries")]
        )
        embed.add_field(
            name="Production countries", value=production_countries, inline=False
        )
        avg_episode_runtime = (
            f"Average episode runtime: {data.get('episode_run_time')[0]} minutes"
        )
        seasons_meta = ""
        for count, value in enumerate(data.get("seasons")):
            seasons_meta += "**{}**. {} ({} episodes) ({})\n".format(
                count + 1,
                value.get("name", "N/A"),
                value.get("episode_count", 0),
                value.get("air_date", "N/A"),
            )
        embed.add_field(
            name="Seasons summary",
            value=f"{seasons_meta}\n{avg_episode_runtime}",
            inline=False,
        )
        if data.get('next_episode_to_air') is not None:
            next_episode_info = (
                f"**S{data.get('next_episode_to_air').get('season_number', 0)}E"
                f"{data.get('next_episode_to_air').get('episode_number', 0)}: "
                f"{data.get('next_episode_to_air').get('name', 'N/A')}**\n"
                f"`air date: {data.get('next_episode_to_air').get('air_date', 'N/A')}`"
            )
            embed.add_field(
                name="Info on next episode", value=next_episode_info, inline=False
            )
        if data.get("tagline", "") != "":
            embed.add_field(name="Tagline", value=data.get("tagline"))
        embed.set_footer(
            text="Information provided by themoviedb API ❤️",
            icon_url="https://i.imgur.com/3K3QMv9.png",
        )

        await ctx.send(embed=embed)
