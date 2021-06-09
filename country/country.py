import asyncio
from urllib.parse import quote

import aiohttp

# Required by Red
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from .iso3166 import ALPHA3_CODES


class Country(commands.Cog):
    """Shows various information and stats about a country through an API."""

    __author__ = "siu3334"
    __version__ = "0.0.6"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\n Author: {self.__author__}\n Cog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def country(self, ctx: commands.Context, *, name: str):
        """Fetch some basic trivia and info about a country."""
        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://restcountries.com/v2/name/{name}") as response:
                        if response.status != 200:
                            return await ctx.send(f"https://http.cat/{response.status}")
                        result = await response.json()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            if isinstance(result, dict):
                return await ctx.send(f"{result['status']} {result['message']}")

            pages = []
            for i, data in enumerate(result):
                embed = discord.Embed(colour=await ctx.embed_color())
                embed.title = data["name"]
                embed.url = "https://en.wikipedia.org/wiki/" + quote(data["name"])
                if data.get("flags"):
                    embed.set_thumbnail(url=[x for x in data["flags"] if x.endswith("png")][0])
                embed.add_field(
                    name="Population", value="~ " + humanize_number(data.get("population", 0))
                )
                if data.get("area"):
                    embed.add_field(name="Area", value=f"~ {humanize_number(data['area'])} km²")
                embed.add_field(name="Calling Code", value="+" + data.get("callingCodes")[0])
                embed.add_field(name="Capital", value=f"\u200b{data.get('capital')}")
                currencies = "\n".join([f"{x['name']} ({x['code']})" for x in data["currencies"]])
                embed.add_field(name="Currency", value=currencies)
                embed.add_field(
                    name="Region / Continent", value=f"{data['region']} / {data['continent']}"
                )
                if data.get("topLevelDomain")[0] != "":
                    embed.add_field(name="Top Level Domain", value=data["topLevelDomain"][0])
                if data.get("gini"):
                    embed.add_field(
                        name="GINI Index",
                        value=f"[{data.get('gini')}](https://en.wikipedia.org/wiki/Gini_coefficient)",
                    )
                if data.get("demonym") != "":
                    embed.add_field(name="Demonym", value=data.get("demonym", "None"))
                embed.add_field(name="Native Name", value=data.get("nativeName", "None"))
                tzones = ", ".join(data.get("timezones"))
                embed.add_field(name="Timezones", value=tzones)
                if data.get("regionalBlocs"):
                    trade_blocs = ", ".join([x.get("name") for x in data["regionalBlocs"]])
                    embed.add_field(name="Part of Trade Bloc", value=trade_blocs)
                if len(embed.fields) in [8, 11]:
                    embed.add_field(name="\u200b", value="\u200b")
                description = ""
                if data.get("borders"):
                    borders = ", ".join([ALPHA3_CODES[x] for x in data["borders"]])
                    description += f"**Shares border with:** {borders}\n"
                if data.get("altSpellings"):
                    alt_names = ", ".join(data["altSpellings"])
                    description += f"**Other Names:** {alt_names}\n"
                embed.description = description
                embed.set_footer(
                    text=f"Page {i + 1} of {len(result)} | Information provided by https://restcountries.com"
                )
                pages.append(embed)

        if len(pages) == 1:
            return await ctx.send(embed=pages[0])
        else:
            await menu(ctx, pages, DEFAULT_CONTROLS, timeout=60.0)
