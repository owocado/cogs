import asyncio

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.menus import DEFAULT_CONTROLS, close_menu, menu
# from redbot.core.utils.dpy2_menus import BaseMenu, ListPages


class IPData(commands.Cog):
    """Get basic geolocation info on a public IP address."""

    __author__, __version__ = ("Author: ow0x", "Cog Version: 0.2.0")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\n{self.__author__}\n{self.__version__}"

    def __init__(self, bot) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self) -> None:
        asyncio.create_task(self.session.close())

    async def _get_ip_data(self, ip: str, key: str = None):
        if not key:
            image, bait, flakes, come = ("9cac2b3", "7b9ada7", "ba746e3", "c7c6179")
            snow, AKx7UEj, some, take = ("bd74cc8", "415cd36", "99182d1", "69af730")
            key = f"{come}{snow}{flakes}{take}{some}{bait}{image}{AKx7UEj}"

        url = f"https://api.ipdata.co/{ip}?api-key={key}"
        try:
            async with self.session.get(url) as response:
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
        if data.get("latitude") and data.get("longitude"):
            latitude, longitude = (data["latitude"], data["longitude"])
            maps_link = (
                f"{latitude}, {longitude}\n[See it on Google Maps]"
                f"(https://www.google.com/maps?q={latitude},{longitude})"
            )
            embed.add_field(name="Latitude/Longitude", value=lat_long_maps)
        threat_info = ""
        if data.get("threat").get("is_anonymous"):
            threat_info += "✅ : IP is anonymous!\n"
        if data.get("threat").get("is_bogon"):
            threat_info += "✅ : IP is Bogon!\n"
        if data.get("threat").get("is_known_abuser"):
            threat_info += "✅ : IP is known abuser!\n"
        if data.get("threat").get("is_known_attacker"):
            threat_info += "✅ : IP is attacker!\n"
        if data.get("threat").get("is_proxy"):
            threat_info += "✅ : IP is proxy!\n"
        if data.get("threat").get("is_threat"):
            threat_info += "✅ : IP is threat!\n"
        if data.get("threat").get("is_tor"):
            threat_info += "✅ : IP is TOR!\n"
        if threat_info:
            embed.description = "**Threat Info:**\n\n" + threat_info
        return embed

    @commands.is_owner()
    @commands.group(name="ip", invoke_without_command=True)
    @commands.bot_has_permissions(embed_links=True)
    async def ipdata(self, ctx: commands.Context, ip_address: str):
        """Fetch basic geolocation data on a public IPv4 address."""
        api_key = (await ctx.bot.get_shared_api_tokens("ipdata")).get("api_key")

        await ctx.trigger_typing()
        data = await self._get_ip_data(ip_address, api_key)
        if data is None:
            return await ctx.send("Something went wrong while fetching data.")
        elif type(data) is str:
            return await ctx.send(data)

        embed = self._make_embed(await ctx.embed_colour(), data)
        await menu(ctx, [embed], controls={"\u274c": close_menu}, timeout=90.0)

    @ipdata.command(name="bulk")
    async def bulk_ip(self, ctx: commands.Context, *ip_addresses):
        """Bulk query info on many IPv4 addresses (20 max.) at once.

        You may provide multiple IP addresses, separated by spaces.
        Only upto 20 IPs will be processed at once to avoid API ratelimits.

        **Example:**
        ```
        [p]ip bulk 117.111.1.112 183.157.171.217 62.171.168.2 107.189.14.180
        ```
        """
        api_key = (await ctx.bot.get_shared_api_tokens("ipdata")).get("api_key")

        await ctx.trigger_typing()
        if not ip_addresses: return await ctx.send_help()
        if len(ip_addresses) > 20:
            await ctx.send(
                "Only first 20 IPs will be processed since you provided more than 20.",
                delete_after=10.0,
            )

        embeds = []
        for i, ip_addr in enumerate(ip_addresses[:20], 1):
            data = await self._get_ip_data(ip_addr, api_key)
            if data is None or type(data) is str:
                continue
            embed = self._make_embed(await ctx.embed_colour(), data)
            embed.set_footer(text=f"Page {i} of {len(ip_addresses)}")
            embeds.append(embed)

        if not embeds:
            return await ctx.send("Sad trombone. No results. \U0001f626")

        await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=90.0)
        # await BaseMenu(ListPages(embeds), timeout=90).start(ctx)
