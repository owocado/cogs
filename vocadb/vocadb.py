import aiohttp
import asyncio
import json

from datetime import datetime
from typing import Any, Dict, Literal

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

BASE_API_URL = "https://vocadb.net/api/songs"

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class VocaDB(commands.Cog):
    """Search for a song on Vocaloid Database (VocaDB) through a query"""

    __author__ = ["siu3334", "<@306810730055729152>"]
    __version__ = "0.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nCog Version: {self.__version__}"

    def __init__(self, bot: Red):
        self.bot = bot

    # credits to jack1142
    async def red_get_data_for_user(self, *, user_id: int) -> Dict[str, Any]:
        # this cog does not story any data
        return {}

    async def red_delete_data_for_user(
        self, *, requester: RequestType, user_id: int
    ) -> None:
        # this cog does not story any data
        pass

    @commands.command()
    async def vocadb(self, ctx, *, query: str):
        """Search for a song on VocaDB"""
        params = {
            "query": query,
            "maxResults": 1,
            "sort": "FavoritedTimes",
            "preferAccurateMatches": "true",
            "nameMatchMode": "Words",
            "fields": "ThumbUrl,Lyrics"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_API_URL, params=params) as response:
                result = await response.json(loads=json.loads)

        data = result["items"][0]
        lyrics = data["lyrics"][0]["value"]
        mins = data["lengthSeconds"] // 60
        secs = data["lengthSeconds"] % 60
        pub_date = data["publishDate"]
        pub_date_strp = datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%SZ")
        pub_date_strf = pub_date_strp.strftime("%A, %d %B, %Y")

        embeds = []
        for page in pagify(lyrics, ["\n"]):
            em = discord.Embed(
                title=f"{data['defaultName']} by {data['artistString']}",
                colour=await ctx.embed_colour(),
            )
            em.url = f"https://vocadb.net/S/{data['id']}"
            em.description = page
            em.set_thumbnail(url=str(data["thumbUrl"]))
            # em.add_field(name="Artist", value=str(data["artistString"]))
            em.add_field(name="Duration", value=f"{mins} minutes, {secs} seconds")
            em.add_field(name="Rating Score", value=str(data['ratingScore']))
            em.add_field(
                name="Favourited",
                value=f"{str(data['favoritedTimes'])} times"
                if data.get("favoritedTimes")
                else "0 times"
            )
            em.set_footer(text=f"Published date: {pub_date_strf}")
            embeds.append(em)

        if not embeds:
            return await ctx.send("No results.")
        elif len(embeds) == 1:
            return await ctx.send(embed=embeds[0])
        else:
            await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=60.0)
