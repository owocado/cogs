import aiohttp

# Required by Red
import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_number, pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS


class Country(commands.Cog):
    """Shows various information and stats about a country through an API."""

    __author__ = "<@306810730055729152>"
    __version__ = "0.0.5"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\n Author: {self.__author__}\n Cog Version: {self.__version__}"

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def country(self, ctx: commands.Context, name: str):
        """Shows various info about a country."""
        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://restcountries.eu/rest/v2/name/{name}"
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                        else:
                            return await ctx.send(f"https://http.cat/{response.status}")
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            embed_list = []
            for data in result:
                embed = discord.Embed(colour=await ctx.embed_color())
                embed.title = data.get("name", "None")
                embed.set_footer(text="Powered by REST Countries API!")
                embed.add_field(
                    name="Population", value=humanize_number(data.get("population", 0))
                )
                embed.add_field(
                    name="Calling Code", value="+" + data.get("callingCodes")[0]
                )
                if data.get("capital") != "":
                    embed.add_field(name="Capital", value=data.get("capital"))
                embed.add_field(
                    name="Currency",
                    value=data.get("currencies")[0].get("name")
                    + " ("
                    + data.get("currencies")[0].get("code")
                    + ")",
                )
                embed.add_field(
                    name="Region / Subregion",
                    value=data.get("region", "None")
                    + " / "
                    + data.get("subregion", "None"),
                )
                embed.add_field(
                    name="Top Level Domain", value=data.get("topLevelDomain")[0]
                )
                if data.get("gini") is not None:
                    embed.add_field(name="GINI Index", value=data.get("gini"))
                if data.get("demonym") != "":
                    embed.add_field(name="Demonym", value=data.get("demonym", "None"))
                embed.add_field(
                    name="Native Name", value=data.get("nativeName", "None")
                )
                if data.get("area") is not None:
                    embed.add_field(
                        name="Approx. Area",
                        value=f"{humanize_number(data.get('area'))} km²",
                        inline=False,
                    )
                tzones = ", ".join(data.get("timezones"))
                embed.add_field(name="Timezones", value=tzones, inline=False)
                if data.get("borders") != []:
                    borders = ", ".join(data.get("borders"))
                    embed.add_field(
                        name="Shares borders with", value=borders, inline=False
                    )
                if data.get("altSpellings"):
                    alt_names = ", ".join(data.get("altSpellings"))
                    embed.add_field(
                        name="Other Names", value=alt_names, inline=False
                    )
                if data.get("regionalBlocs"):
                    blocs = ", ".join(
                        [x.get("name") for x in data.get("regionalBlocs")]
                    )
                    embed.add_field(
                        name="Part of Trade Bloc", value=blocs, inline=False
                    )
                embed.set_thumbnail(
                    url=f"https://www.countryflags.io/{data.get('alpha2Code')}/flat/64.png"
                )
                embed_list.append(embed)

        if not embed_list:
            return await ctx.send("No results.")
        elif len(embed_list) == 1:
            return await ctx.send(embed=embed_list[0])
        else:
            await menu(ctx, embed_list, DEFAULT_CONTROLS, timeout=60.0)
