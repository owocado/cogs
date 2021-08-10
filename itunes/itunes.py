import asyncio
import json
from datetime import datetime

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.menus import close_menu, menu, DEFAULT_CONTROLS


class iTunes(commands.Cog):
    """Search for a song on Apple iTunes."""

    __author__ = "ow0x (<@306810730055729152>)"
    __version__ = "0.0.2"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def itunes(self, ctx: commands.Context, country: str, *, query: str):
        """Fetch various info about a song from Apple iTunes.

        For `country` parameter, you need to pass an ISO_639-1 country code:
        https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
        """
        await ctx.trigger_typing()
        base_url = "https://itunes.apple.com/search"
        params = {
            "term": query,
            "media": "music",
            "entity": "song",
            "limit": 10,
            "explicit": "yes" if ctx.channel.is_nsfw() else "no",
            "country": country
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    results = json.loads(await response.read())
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        if len(results.get("results")) == 0:
            return await ctx.send("No results.")

        pages = []
        for i, data in enumerate(results.get("results")):
            embed = discord.Embed(colour=await ctx.embed_colour())
            embed.title = data.get("trackName", "Unknown track")
            embed.url = data.get("trackViewUrl")
            embed.set_author(
                name="Apple iTunes",
                url="https://www.apple.com/itunes/",
                icon_url="https://i.imgur.com/PR29ow0.jpg",
            )
            embed.set_thumbnail(url=data.get("artworkUrl100").replace("100", "500"))
            embed.add_field(name="Artist", value=data.get("artistName"))
            embed.add_field(name="Album", value=data.get("collectionName"))
            release_date = datetime.strptime(data.get("releaseDate"), "%Y-%m-%dT%H:%M:%SZ").strftime("%d %b, %Y")
            embed.add_field(name="Release Date", value=release_date)
            embed.add_field(name="Genre", value=data.get("primaryGenreName"))
            minutes = data.get("trackTimeMillis", 0) // 60000
            seconds = data.get("trackTimeMillis", 0) % 60
            embed.add_field(name="Track Length", value=f"{minutes}m {seconds}s")
            embed.add_field(name="Track Price", value=f"{data.get('trackPrice')} {data.get('currency')}")
            embed.set_footer(text=f"Page {i + 1} of {results.get('resultCount')}")
            pages.append(embed)

        controls = {"❌": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=60.0)
