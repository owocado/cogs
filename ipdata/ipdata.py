import asyncio

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.menus import DEFAULT_CONTROLS, close_menu, menu
# from redbot.core.utils.dpy2_menus import BaseMenu, ListPages


class IPData(commands.Cog):
    """Get basic geolocation info on a public IP address."""

    __author__, __version__ = ("Author: ow0x", "Cog Version: 0.1.0")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\n{self.__author__}\n{self.__version__}"

    @staticmethod
    async def _get_ip_data(url: str):
        try:
            async with aiohttp.request("GET", url) as response:
                if response.status in [400, 401, 403]:
                    return (await response.json())["message"]
                elif response.status != 200:
                    return None
                return await response.json()
        except asyncio.TimeoutError:
            return None

    @staticmethod
    def _make_embed(meta, data) -> discord.Embed:
        embed = discord.Embed(color=meta)
        embed.set_author(
            name=f"Info for IP: {data.get('ip')}", icon_url=data.get("flag") or "",
        )
        if data.get("asn"):
            embed.add_field(name="ASN (ISP)", value="\u200b" + data["asn"].get("name", "N/A"))
            embed.add_field(name="ASN Type", value=str(data["asn"].get("type").upper()))
            embed.add_field(name="ASN Domain", value=str(data["asn"].get("domain")))
            embed.add_field(name="ASN Route", value=str(data["asn"].get("route")))
        if data.get("city"):
            embed.add_field(name="City", value=str(data.get("city")))
        if data.get("region"):
            embed.add_field(name="Region", value=str(data.get("region")))
        if data.get("country_name"):
            embed.add_field(name="Country", value=str(data.get("country_name")))
        if data.get("continent_name"):
            embed.add_field(name="Continent", value=str(data.get("continent_name")))
        if data.get("calling_code"):
            embed.add_field(name="Calling Code", value="+" + str(data.get("calling_code")))
        lat_long_maps = (
            f"{data.get('latitude')}, {data.get('longitude')}\n"
            "[See it on Google Maps](https://www.google.com/maps?q="
            f"{data.get('latitude')},{data.get('longitude')})"
        )
        if data.get("latitude") and data.get("longitude"):
            embed.add_field(name="Latitude/Longitude", value=lat_long_maps)
        threat_info = ""
        if data.get("threat").get("is_anonymous"):
            threat_info += "✅ : Is anonymous!\n"
        if data.get("threat").get("is_bogon"):
            threat_info += "✅ : Is Bogon!\n"
        if data.get("threat").get("is_known_abuser"):
            threat_info += "✅ : Is known abuser!\n"
        if data.get("threat").get("is_known_attacker"):
            threat_info += "✅ : Is attacker!\n"
        if data.get("threat").get("is_proxy"):
            threat_info += "✅ : Is proxy!\n"
        if data.get("threat").get("is_threat"):
            threat_info += "✅ : Is threat!\n"
        if data.get("threat").get("is_tor"):
            threat_info += "✅ : Is TOR!\n"
        if threat_info:
            embed.description = "**Threat Info:**\n\n" + threat_info
        return embed

    @commands.is_owner()
    @commands.group(name="ip", invoke_without_command=True)
    @commands.bot_has_permissions(embed_links=True)
    async def ipdata(self, ctx: commands.Context, ip_address: str):
        """Fetch basic geolocation data on a public IP address."""
        api_key = (await ctx.bot.get_shared_api_tokens("ipdata")).get("api_key")
        if api_key is None:
            api_key = "a01cfa2e81e015d3e07c65b13d199cdc9e7c4f7fa4e4a3c3bdea3923"

        await ctx.trigger_typing()
        base_url = f"https://api.ipdata.co/{ip_address}?api-key={api_key}"
        data = await self._get_ip_data(base_url)
        if data is None:
            return await ctx.send("Something went wrong while fetching data.")
        elif type(data) is str:
            return await ctx.send(data)

        embed = self._make_embed(await ctx.embed_colour(), data)
        await menu(ctx, [embed], controls={"\u274c": close_menu}, timeout=90.0)

    @ipdata.command(name="bulk")
    async def bulk_ip(self, ctx: commands.Context, *ip_addresses):
        """Bulk query info on many IP addresses (10 max.) at once.

        You may provide multiple IP addresses, separated by spaces.

        **Example:**
        ```
        [p]ip bulk 117.111.1.112 183.157.171.217 62.171.168.2
        ```
        """
        await ctx.trigger_typing()
        if not ip_addresses: return await ctx.send_help()
        if len(ip_addresses) > 10:
            return await ctx.send("Upto max. 10 IP addresses can be queried at once.")

        api_key = (await ctx.bot.get_shared_api_tokens("ipdata")).get("api_key")
        if api_key is None:
            api_key = "a01cfa2e81e015d3e07c65b13d199cdc9e7c4f7fa4e4a3c3bdea3923"

        embeds = []
        for i, ip_addr in enumerate(ip_addresses, 1):
            data = await self._get_ip_data(f"https://api.ipdata.co/{ip_addr}?api-key={api_key}")
            if data is None or type(data) is str:
                continue
            embed = self._make_embed(await ctx.embed_colour(), data)
            embed.set_footer(text=f"Page {i} of {len(ip_addresses)}")
            embeds.append(embed)

        if not embeds:
            return await ctx.send("Sad trombone. No results. \U0001f626")

        await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=90.0)
        # await BaseMenu(ListPages(embeds), timeout=90).start(ctx)