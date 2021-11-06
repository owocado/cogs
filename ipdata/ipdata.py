import asyncio

import aiohttp
import discord
from redbot.core import commands


class IPData(commands.Cog):
    """IP Geolocation and Proxy Detection cog."""

    __author__ = "ow0x"
    __version__ = "0.0.11"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def ip(self, ctx: commands.Context, ip_address: str):
        """Fetch various geolocation data about a provided public IP address."""
        api_key = (await ctx.bot.get_shared_api_tokens("ipdata")).get("api_key")
        if api_key is None:
            api_key = "a01cfa2e81e015d3e07c65b13d199cdc9e7c4f7fa4e4a3c3bdea3923"

        await ctx.trigger_typing()
        base_url = f"https://api.ipdata.co/{ip_address}?api-key={api_key}"
        try:
            async with aiohttp.request("GET", base_url) as response:
                if response.status in [400, 401, 403]:
                    return await ctx.send((await response.json())["message"])
                elif response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                data = await response.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        embed = discord.Embed(color=await ctx.embed_colour())
        embed.set_author(
            name=f"Info for IP: {data.get('ip')}",
            icon_url=data.get("flag") or "",
        )
        if data.get("asn"):
            embed.add_field(name="ASN (ISP)", value="\u200b" + str(data["asn"].get("name")))
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
            + "[See it on Google Maps](https://www.google.com/maps?q="
            + f"{data.get('latitude')},{data.get('longitude')})"
        )
        embed.add_field(name="Latitude/Longitude", value=lat_long_maps)
        threat_info = ""
        if data.get("threat").get("is_anonymous"):
            threat_info += "✅ : Is anonymous!"
        if data.get("threat").get("is_bogon"):
            threat_info += "✅ : Is Bogon?"
        if data.get("threat").get("is_known_abuser"):
            threat_info += "✅ : Is known abuser!"
        if data.get("threat").get("is_known_attacker"):
            threat_info += "✅ : Is attacker!"
        if data.get("threat").get("is_proxy"):
            threat_info += "✅ : Is proxy!"
        if data.get("threat").get("is_threat"):
            threat_info += "✅ : Is threat!"
        if data.get("threat").get("is_tor"):
            threat_info += "✅ : Is TOR!"
        embed.description = "**Threat Info:**\n\n" + threat_info

        await ctx.send(embed=embed)
