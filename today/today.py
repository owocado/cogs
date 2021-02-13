import aiohttp
from random import choice
from typing import Any, Dict, Literal

# Required by Red
import discord
from redbot.core import checks, commands
from redbot.core.bot import Red

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class Today(commands.Cog):
    """Various commands to show the stats about users' profile badges."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.0.3"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot: Red):
        self.bot = bot

    # credits to jack1142
    async def red_get_data_for_user(self, *, user_id: int) -> Dict[str, Any]:
        # this cog does not story any data
        return {}

    # credits to jack1142
    async def red_delete_data_for_user(
        self, *, requester: RequestType, user_id: int
    ) -> None:
        # this cog does not story any data
        pass

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def today(self, ctx: commands.Context):
        """Responds with random fact on what happened today in history."""
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://history.muffinlabs.com/date") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        link = data.get("url", "None")
                        today = data.get("date", "None")

                        pick = choice(data["data"]["Events"])
                        year = pick.get("year", "None")
                        text = pick.get("text", "None")

                        em = discord.Embed(colour=await ctx.embed_color())
                        em.title = f"On this day ({today}) ..."
                        em.url = str(link)
                        em.description = f"\u200b\nIn {year} : {text}\n\u200b"
                        return await ctx.send(embed=em)
                    else:
                        await ctx.send(f"API returned status code: {resp.status}")
