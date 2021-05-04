import aiohttp
import asyncio

import discord
from redbot.core import commands


class IPData(commands.Cog):
    """IP Geolocation and Proxy Detection cog."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.0.6"

    def __init__(self, bot):
        self.bot = bot

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    @commands.command()
    @commands.is_owner()
    @commands.bot_has_permissions(embed_links=True)
    async def ip(self, ctx: commands.Context, ip_address: str):
        """Returns various info about provided IP.

        Please note that this command requires an API key.
        You can get one by signing up at :
        https://ipdata.co/sign-up.html

        Once you received API key, set it with:
        ```
        [p]set api ipdata api_key <api_key>
        ```
        """
        api_key = (await ctx.bot.get_shared_api_tokens("ipdata")).get("api_key")
        if not api_key:
            return await ctx.send_help()
        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://api.ipdata.co/{ip_address}?api-key={api_key}") as response:
                        if response.status != 200:
                            return await ctx.send(f"https://http.cat/{response.status}")
                        data = await response.json()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            em = discord.Embed(color=await ctx.embed_colour())
            em.set_author(
                name=f"Info for IP: {data.get('ip')}",
                icon_url=str(data.get("flag")),
            )
            em.add_field(name="ASN (Carrier)", value=str(data.get("asn").get("name")))
            em.add_field(name="ASN Type", value=str(data.get("asn").get("type")))
            em.add_field(name="ASN Domain", value=str(data.get("asn").get("domain")))
            em.add_field(name="ASN Route", value=str(data.get("asn").get("route")))
            em.add_field(name="City", value=str(data.get("city")))
            em.add_field(name="Region", value=str(data.get("region")))
            em.add_field(name="Country", value=str(data.get("country_name")))
            em.add_field(name="Continent", value=str(data.get("continent_name")))
            em.add_field(name="Calling Code", value=str(data.get("calling_code")))
            threat_info = "\u200b"
            if data.get("threat").get("is_anonymous"):
                threat_info += "Is anonymous? \N{WHITE HEAVY CHECK MARK}"
            if data.get("threat").get("is_bogon"):
                threat_info += "Is Bogon? \N{WHITE HEAVY CHECK MARK}"
            if data.get("threat").get("is_known_abuser"):
                threat_info += "Is Known abuser? \N{WHITE HEAVY CHECK MARK}"
            if data.get("threat").get("is_known_attacker"):
                threat_info += "Is attacker? \N{WHITE HEAVY CHECK MARK}"
            if data.get("threat").get("is_proxy"):
                threat_info += "Is proxy? \N{WHITE HEAVY CHECK MARK}"
            if data.get("threat").get("is_threat"):
                threat_info += "Is threat? \N{WHITE HEAVY CHECK MARK}"
            if data.get("threat").get("is_tor"):
                threat_info += "Is TOR? \N{WHITE HEAVY CHECK MARK}"
            em.description = threat_info

            await ctx.send(embed=em)
