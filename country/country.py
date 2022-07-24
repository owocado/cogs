import asyncio
from urllib.parse import quote

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .api import CountryData, NotFound


class Country(commands.Cog):
    """Shows basic statistics and info about a country."""

    __authors__ = ["ow0x"]
    __version__ = "2.0.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(self.__authors__)}\n"
            f"**Cog version:**  v{self.__version__}"
        )

    session = aiohttp.ClientSession()

    def cog_unload(self) -> None:
        if self.session:
            asyncio.create_task(self.session.close())

    @commands.command()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def country(self, ctx: commands.Context, *, name: str):
        """Fetch basic summary info about a country."""
        async with ctx.typing():
            result = await CountryData.request(self.session, name)
            if isinstance(result, NotFound):
                return await ctx.send(f"❌ Error: {result}! {result.image}")

            pages = []
            for i, data in enumerate(result, start=1):
                colour = await ctx.embed_colour()
                footer = f"Page {i} of {len(result)} | Data provided by RestCountries.com"
                embed = self.country_embed(data, colour, footer)
                pages.append(embed)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=90.0)

    @staticmethod
    def country_embed(data: CountryData, colour: discord.Colour, footer: str) -> discord.Embed:
        emb = discord.Embed(colour=colour)
        emb.set_author(name=data.name)
        wiki_link = f"https://en.wikipedia.org/wiki/{quote(data.name)}"
        alt_names = ""
        emb.set_thumbnail(url=data.png_flag)
        if data.altSpellings:
            sep = '\n' if len(data.altSpellings) > 2 else ' '
            alt_names += f"**Commonly known as:** {sep}{', '.join(data.altSpellings)}\n\n"
        emb.description = alt_names + f"**[See Wikipedia page!]({wiki_link})**"
        emb.add_field(name="Population", value=f"≈ {data.inhabitants}")
        if data.area:
            emb.add_field(name="Estimated Area", value=f"{humanize_number(data.area)} sq. km.")
        emb.add_field(name="Calling Code(s)", value=data.calling_codes)
        emb.add_field(name="Capital", value=str(data.capital))
        # "continent" key was changed to "region" now in API!
        emb.add_field(name="Continent", value=data.subregion)
        # Fix for Antarctica
        if data.currencies:
            emb.add_field(name="Currency", value=', '.join(str(c) for c in data.currencies))
        if data.tld:
            emb.add_field(name="Top Level Domain", value=data.tld)
        if data.gini:
            gini_wiki = "https://en.wikipedia.org/wiki/Gini_coefficient"
            emb.add_field(name="GINI Index", value=f"[{data.gini}]({gini_wiki})")
        if data.demonym:
            emb.add_field(name="Demonym", value=data.demonym)
        if data.regionalBlocs:
            emb.add_field(name="Trade Bloc", value=data.trade_blocs)
        emb.add_field(name="Timezones", value=', '.join(data.timezones))
        if len(emb.fields) in {8, 11}:
            emb.add_field(name="\u200b", value="\u200b")
        if data.borders:
            noun = 'countries' if len(data.borders) > 1 else 'country'
            emb.add_field(
                name=f"Shares {len(data.borders)} borders | with:",
                value=data.shared_borders,
                inline=False
            )
        emb.set_footer(text=footer)
        return emb
