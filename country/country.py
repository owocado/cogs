import asyncio
from urllib.parse import quote

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.menus import DEFAULT_CONTROLS, close_menu, menu
# from redbot.core.utils.dpy2_menus import BaseMenu, ListPages

from .iso3166 import ALPHA3_CODES


class Country(commands.Cog):
    """Shows basic statistics and info about a country."""

    __author__ , __version__ = ("Author: ow0x", "Cog Version: 0.1.0")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\n{self.__author__}\n{self.__version__}"

    @commands.command()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def country(self, ctx: commands.Context, *, name: str):
        """Fetch some basic statistics and info about a country."""
        await ctx.trigger_typing()
        try:
            async with aiohttp.request("GET", f"https://restcountries.com/v2/name/{name}") as resp:
                    if resp.status != 200:
                        return await ctx.send(f"https://http.cat/{resp.status}")
                    result = await resp.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        if isinstance(result, dict):
            return await ctx.send(f"{result['status']} {result['message']}")

        pages = []
        for i, data in enumerate(result, start=1):
            colour = await ctx.embed_colour()
            footer = f"Page {i} of {len(result)} • Powered by restcountries.com"
            embed = self.country_embed(colour, footer, data)
            pages.append(embed)

        controls = {"": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=90.0)
        # await BaseMenu(ListPages(pages), ctx=ctx).start(ctx)

    @staticmethod
    def country_embed(colour, footer, data):
        embed = discord.Embed(colour=colour, title=data.get("name", ""))
        embed.url = "https://en.wikipedia.org/wiki/" + quote(data["name"])
        if data.get("flags"):
            embed.set_thumbnail(url=data["flags"].get("png", ""))
        embed.add_field(name="Population", value=humanize_number(data.get("population", 0)))
        if data.get("area"):
            embed.add_field(name="Area", value=f"{humanize_number(data['area'])} km²")
        embed.add_field(name="Calling Code", value="+" + data.get("callingCodes")[0])
        embed.add_field(name="Capital", value=f"\u200b{data.get('capital')}")
        # Fix for Antarctica
        if data.get("currencies"):
            currencies = "\n".join([f"{x['name']} ({x['code']})" for x in data["currencies"]])
            embed.add_field(name="Currency", value=currencies)
        # "continent" key was changed to "region" now in API!
        embed.add_field(name="Region / Continent", value=f"{data['subregion']} / {data.get('region', '')}")
        if data.get("topLevelDomain")[0] != "":
            embed.add_field(name="Top Level Domain", value=data["topLevelDomain"][0])
        if data.get("gini"):
            wikilink = "https://en.wikipedia.org/wiki/Gini_coefficient"
            embed.add_field(name="GINI Index", value=f"[{data.get('gini')}]({wikilink})")
        if data.get("demonym"):
            embed.add_field(name="Demonym", value=data.get("demonym", "None"))
        embed.add_field(name="Native Name", value=data.get("nativeName", "None"))
        tzones = ", ".join(data.get("timezones"))
        embed.add_field(name="Timezones", value=tzones)
        if data.get("regionalBlocs"):
            trade_blocs = ", ".join([x.get("name") for x in data["regionalBlocs"]])
            embed.add_field(name="Part of Trade Bloc", value=trade_blocs)
        if len(embed.fields) in {8, 11}:
            embed.add_field(name="\u200b", value="\u200b")
        description = ""
        if data.get("borders"):
            borders = "\n".join([f"`[{i}]` {ALPHA3_CODES[x]}" for i, x in enumerate(data["borders"], 1)])
            description += f"**Shares borders with:**\n{borders}\n\n"
        if data.get("altSpellings"):
            description += f"**Other Names:** {', '.join(data['altSpellings'])}\n"
        embed.description = description
        embed.set_footer(text=footer)
        return embed
