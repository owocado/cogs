import aiohttp
import asyncio

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box


class IPData(commands.Cog):
    """IP Geolocation and Proxy Detection cog."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.0.8"

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
        """Fetch various geolocation data about a provided public IP address.

        Please note that this command requires an API key.
        You can get one for free by signing up at :
        https://ipdata.co/sign-up.html

        Once you received API key, set it with:
        ```
        [p]set api ipdata api_key <api_key>
        ```
        """
        api_key = (await ctx.bot.get_shared_api_tokens("ipdata")).get("api_key")
        if not api_key:
            return await ctx.send_help()

        await ctx.trigger_typing()
        base_url = f"https://api.ipdata.co/{ip_address}?api-key={api_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    data = await response.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        embed = discord.Embed(color=await ctx.embed_colour())
        embed.set_author(
            name=f"Info for IP: {data.get('ip')}",
            icon_url=str(data.get("flag")),
        )
        if data.get("asn"):
            embed.add_field(name="ASN (Carrier)", value=str(data["asn"].get("name")))
            embed.add_field(name="ASN Type", value=str(data["asn"].get("type").upper()))
            embed.add_field(name="ASN Domain", value=str(data["asn"].get("domain")))
            embed.add_field(name="ASN Route", value=str(data["asn"].get("route")))
        embed.add_field(name="City", value=str(data.get("city")))
        embed.add_field(name="Region", value=str(data.get("region")))
        embed.add_field(name="Country", value=str(data.get("country_name")))
        embed.add_field(name="Continent", value=str(data.get("continent_name")))
        embed.add_field(name="Calling Code", value="+" + str(data.get("calling_code")))
        lat_long_maps = (
            f"{data.get('latitude')}, {data.get('longitude')}\n"
            "[See it on Google Maps](https://www.google.com/maps?q="
            f"{data.get('latitude')},{data.get('longitude')})"
        )
        embed.add_field(name="Latitude/Longitude", value=lat_long_maps)
        threat_info = "\u200b"
        if data.get("threat").get("is_anonymous"):
            threat_info += "Is anonymous? : ✅\n"
        if data.get("threat").get("is_bogon"):
            threat_info += "Is Bogon?     : ✅\n"
        if data.get("threat").get("is_known_abuser"):
            threat_info += "Known abuser? : ✅\n"
        if data.get("threat").get("is_known_attacker"):
            threat_info += "Is attacker?  : ✅\n"
        if data.get("threat").get("is_proxy"):
            threat_info += "Is proxy?     : ✅\n"
        if data.get("threat").get("is_threat"):
            threat_info += "Is threat?    : ✅\n"
        if data.get("threat").get("is_tor"):
            threat_info += "Is TOR?       : ✅\n"
        embed.description = box(threat_info)

        await ctx.send(embed=embed)
