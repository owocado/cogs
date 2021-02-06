import aiohttp
from typing import Any, Dict, Literal

# Required by Red
import discord
from redbot.core import checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_number, pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class Country(commands.Cog):
    """Various commands to show the stats about users' profile badges."""

    __author__ = ["siu3334", "<@306810730055729152>"]
    __version__ = "0.0.3"

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

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def country(self, ctx: commands.Context, name: str):
        """Shows various info about a country."""

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://restcountries.eu/rest/v2/name/{name}") as response:
                result = await response.json()

        embed_list = []
        for data in result:
            embed = discord.Embed(colour=await ctx.embed_color())
            embed.title = data["name"]
            embed.set_footer(text="Powered by REST Countries API!")
            embed.add_field(name="Population", value=humanize_number(data["population"]))
            embed.add_field(name="Calling Code", value=f"\u200b{data['callingCodes'][0]}")
            embed.add_field(name="Capital", value=f"\u200b{data['capital']}")
            embed.add_field(name="Currency", value=data["currencies"][0]["name"])
            embed.add_field(
                name="Region / Subregion",
                value=f"{data.get('region', 'None')} / {data.get('subregion', 'None')}",
            )
            embed.add_field(name="Top Level Domain", value=data["topLevelDomain"][0])
            if data["gini"] is not None:
                embed.add_field(name="GINI Index", value=data.get("gini", "None"))
            embed.add_field(name="Demonym", value=data.get("demonym", "None"))
            embed.add_field(name="Native Name", value=data.get("nativeName", "None"))
            if data["area"] is not None:
                embed.add_field(name="Approx. Area", value=f"{humanize_number(data['area'])} km²", inline=False)
            tzones = ", ".join(x for x in data["timezones"])
            embed.add_field(name="Timezones", value=f"{tzones}", inline=False)
            if data["borders"]:
                borders = ", ".join(x for x in data["borders"])
                embed.add_field(name="Shares borders with", value=f"{borders}", inline=False)
            if data["altSpellings"]:
                altnames = ", ".join(x for x in data["altSpellings"])
                embed.add_field(name="Other Names", value=f"{altnames}", inline=False)
            if data["regionalBlocs"]:
                embed.add_field(name="Part of Trade Bloc", value=data["regionalBlocs"][0]["name"], inline=False)
            embed.set_thumbnail(url=f"https://www.countryflags.io/{data['alpha2Code']}/flat/64.png")
            embed_list.append(embed)

        if not embed_list:
            return await ctx.send("No results.")
        elif len(embed_list) == 1:
            return await ctx.send(embed=embed_list[0])
        else:
            await menu(ctx, embed_list, DEFAULT_CONTROLS, timeout=60.0)
