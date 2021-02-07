import aiohttp
from typing import Any, Dict, Literal

# Required by Red
import discord
from redbot.core import checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_number, pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class SteamCog(commands.Cog):
    """Show various info about a Steam game."""

    __author__ = ["siu3334", "<@306810730055729152>"]
    __version__ = "0.0.4"

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

    # credits to jack1142
    async def red_delete_data_for_user(
        self, *, requester: RequestType, user_id: int
    ) -> None:
        # this cog does not story any data
        pass

    # Logic taken from https://github.com/TrustyJAID/Trusty-cogs/blob/master/notsobot/notsobot.py#L221
    # Credits to Trusty <3
    async def fetch_appid(self, query: str):
        url = f"https://store.steampowered.com/api/storesearch?cc=us&l=en&term={query}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

        appid = data["items"][0]["id"]
        return appid

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def steam(self, ctx: commands.Context, query: str):
        """Show various info about a Steam game."""

        appid = await self.fetch_appid(query)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://store.steampowered.com/api/appdetails?appids={appid}") as resp:
                data = await resp.json()

        embed_list = []
        embed = discord.Embed(
            title=data[f"{appid}"]["data"]["name"],
            colour=await ctx.embed_color(),
        )
        embed.url = f"https://store.steampowered.com/app/{appid}"
        embed.set_image(url=str(data[f"{appid}"]["data"]["header_image"]).replace('\\', ''))
        if data[f"{appid}"]["data"]["price_overview"]:
            embed.add_field(name="Game Price", value=data[f"{appid}"]["data"]["price_overview"]["final_formatted"])
        embed.add_field(name="Release Date", value=data[f"{appid}"]["data"]["release_date"]["date"])
        embed.add_field(name="Metascore", value=data[f"{appid}"]["data"]["metacritic"]["score"])
        embed.add_field(name="Recommendations", value=humanize_number(data[f"{appid}"]["data"]["recommendations"]["total"]))
        embed.add_field(name="Achievements", value=data[f"{appid}"]["data"]["achievements"]["total"])
        if data[f"{appid}"]["data"]["dlc"]:
            embed.add_field(name="DLC Count", value=len(data[f"{appid}"]["data"]["dlc"]))
        embed.add_field(name="Developers", value=data[f"{appid}"]["data"]["developers"][0])
        embed_list.append(embed)

        if not embed_list:
            return await ctx.send("No results.")
        elif len(embed_list) == 1:
            return await ctx.send(embed=embed_list[0])
        else:
            await menu(ctx, embed_list, DEFAULT_CONTROLS, timeout=60.0)
