import aiohttp
import asyncio
import json

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import bold, humanize_number

USER_AGENT = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36"
}


class RottenTomatoes(commands.Cog):
    """Get rottentomatoes reviews and ratings for a movie query."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    async def fetch_movie_id(self, ctx: commands.Context, query: str):
        url = "https://www.rottentomatoes.com/api/private/v2.0/search"
        params = {"limit": 10, "q": query}
        try:
            async with self.session.get(url, params=params, headers=USER_AGENT) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        except asyncio.TimeoutError:
            return None

        if len(data.get("movies")) == 0:
            return None
        elif len(data.get("movies")) == 1:
            movie_id = data.get("movies")[0].get("url").replace("/m/", "")
            return movie_id
        elif len(data.get("movies")) > 1:
            # This logic taken from https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
            # All credits belong to Sitryk, I do not take any credit for this code.
            items = ""
            for count, value in enumerate(data.get("movies")):
                items += "**{}.** {} ({})\n".format(
                    count + 1,
                    value.get("name", "Movie title missing"),
                    value.get("year", "N/A"),
                )
            choices = f"Found multiple results for your game query. Please select one from:\n\n{items}"
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
                movie_id = data.get("movies")[choice].get("url").replace("/m/", "")
                await send_to_channel.delete()
                return movie_id
        else:
            return None

    @commands.command(aliases=["rtomato"])
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def rottentomatoes(self, ctx: commands.Context, *, query: str):
        """Show various info about a Steam game."""
        async with ctx.typing():
            movie_id = await self.fetch_movie_id(ctx, query)
            if movie_id is None:
                return await ctx.send(
                    "No results found or API gateway timed out (504)."
                )

            base_url = (
                f"https://www.rottentomatoes.com/api/private/v1.0/movies/{movie_id}"
            )
            try:
                async with self.session.get(base_url, headers=USER_AGENT) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    data = json.loads(await response.read())
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            em = discord.Embed(colour=0xC52404)
            em.title = data.get("title", "Missing movie title")
            em.url = f"https://www.rottentomatoes.com/m/{data.get('vanity', '')}"
            em.description = (
                f"**Consensus:** {data.get('ratingSummary').get('consensus')}"
            )
            em.set_author(
                name="Rotten Tomatoes", icon_url="https://i.imgur.com/NGxHSXX.png"
            )
            if data.get("posters"):
                em.set_thumbnail(url=data.get("posters").get("original"))
            tomato_meter = "\u200b"
            if (
                data.get("ratingSummary")
                and data.get("ratingSummary").get("allCritics")
                and data.get("ratingSummary").get("allCritics").get("meterValue")
            ):
                tomato_meter += (
                    f"{data.get('ratingSummary').get('allCritics').get('meterValue')}% "
                    f"({humanize_number(data.get('ratingSummary').get('allCritics').get('numReviews'))} reviews)"
                )
            em.add_field(name="Tomato Meter", value=tomato_meter)
            audience_score = "\u200b"
            if (
                data.get("ratingSummary")
                and data.get("ratingSummary").get("audience")
                and data.get("ratingSummary").get("audience").get("meterScore")
            ):
                audience_score += (
                    f"{data.get('ratingSummary').get('audience').get('meterScore')}% "
                    f"({humanize_number(data.get('ratingSummary').get('audience').get('numTotal'))} ratings)"
                )
            em.add_field(name="Audience Score", value=audience_score)
            average_rating = "\u200b"
            if (
                data.get("ratingSummary")
                and data.get("ratingSummary").get("audience")
                and data.get("ratingSummary").get("audience").get("averageScore")
            ):
                average_rating += f"{bold(str(round(data.get('ratingSummary').get('audience').get('averageScore'), 2)))} out of **5** ⭐"
            em.add_field(name="Average Rating", value=average_rating)
            if data.get("mpaaRating"):
                em.add_field(
                    name="MPAA Rating", value="\u200b" + data.get("mpaaRating")
                )
            if data.get("boxoffice"):
                em.add_field(name="Box Office", value="\u200b" + data.get("boxoffice"))
            if data.get("runningTimeStr"):
                em.add_field(
                    name="Runtime", value="\u200b" + data.get("runningTimeStr")
                )
            if data.get("advisory"):
                em.add_field(name="Advisory", value="\u200b" + data.get("advisory"))

            await ctx.send(embed=em)
