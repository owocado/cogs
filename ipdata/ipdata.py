import logging

from ipdata import ipdata
from typing import Any, Dict, Literal

import aiohttp
import discord
from redbot.core import checks, commands

log = logging.getLogger("red.owo-cogs.ipdata")

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


# Taken from https://github.com/flaree/Flare-Cogs/blob/master/dankmemer/dankmemer.py#L16
# Many thanks to flare <3
async def tokencheck(ctx):
    token = await ctx.bot.get_shared_api_tokens("ipdata")
    return bool(token.get("api_key"))


class IPData(commands.Cog):
    """IP Geolocation and Proxy Detection cog."""

    __author__ = "siu3334"
    __version__ = "0.0.5"

    def __init__(self, bot):
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

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """
        Thanks Sinbad!
        """
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nCog Version: {self.__version__}"

    @commands.is_owner()
    @commands.check(tokencheck)
    @commands.command(aliases=["ipdata"])
    @checks.bot_has_permissions(embed_links=True)
    async def ip(self, ctx: commands.Context, ip: str):
        """Returns various info about provided IP."""
        api = await ctx.bot.get_shared_api_tokens("ipdata")
        key = api.get("api_key")
        ipdata = ipdata.IPData(str(key))
        response = ipdata.lookup(ip)

        try:
            em = discord.Embed(color=await ctx.embed_colour())
            em.set_author(
                name=f"Info for IP: {response.get('ip')}",
                icon_url=str(response.get("flag")),
            )
            em.add_field(name="ASN (Carrier)", value=str(response.get("asn").get("name")))
            em.add_field(name="ASN Type", value=str(response.get("asn").get("type")))
            em.add_field(name="ASN Domain", value=str(response.get("asn").get("domain")))
            em.add_field(name="ASN Route", value=str(response.get("asn").get("route")))
            em.add_field(name="City", value=str(response.get("city")))
            em.add_field(name="Region", value=str(response.get("region")))
            em.add_field(name="Country", value=str(response.get("country_name")))
            em.add_field(name="Continent", value=str(response.get("continent_name")))
            em.add_field(name="Calling Code", value=str(response.get("calling_code")))
            threat_info = "\u200b"
            if response.get("threat").get("is_anonymous"):
                threat_info += "Is anonymous? \N{WHITE HEAVY CHECK MARK}"
            if response.get("threat").get("is_bogon"):
                threat_info += "Is Bogon? \N{WHITE HEAVY CHECK MARK}"
            if response.get("threat").get("is_known_abuser"):
                threat_info += "Is Known abuser? \N{WHITE HEAVY CHECK MARK}"
            if response.get("threat").get("is_known_attacker"):
                threat_info += "Is attacker? \N{WHITE HEAVY CHECK MARK}"
            if response.get("threat").get("is_proxy"):
                threat_info += "Is proxy? \N{WHITE HEAVY CHECK MARK}"
            if response.get("threat").get("is_threat"):
                threat_info += "Is threat? \N{WHITE HEAVY CHECK MARK}"
            if response.get("threat").get("is_tor"):
                threat_info += "Is TOR? \N{WHITE HEAVY CHECK MARK}"
            em.description = threat_info
            return await ctx.send(embed=em)
        except ValueError as e:
            await ctx.send(str(e))
