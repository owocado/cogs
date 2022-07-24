import asyncio

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .api import IPData


class IPInfo(commands.Cog):
    """Get basic geolocation info on a public IP address."""

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

    @staticmethod
    def _make_embed(data: IPData, color: discord.Colour) -> discord.Embed:
        embed = discord.Embed(color=color)
        embed.description = f"__**Threat Info:**__\n\n{data.threat}" if data.threat else ""
        embed.set_author(name=f"Info for IP: {data.ip}", icon_url=data.flag or "")
        if data.asn:
            embed.add_field(name="ASN Carrier", value=str(data.asn))
            embed.add_field(name="ASN Route", value=f"{data.asn.route}\n{data.asn.domain or ''}")
        if data.city:
            embed.add_field(name="City / Region", value=f"{data.city}\n{data.region or ''}")
        if data.country_name:
            embed.add_field(name="Country / Continent", value=data.country)
        if data.calling_code:
            embed.add_field(name="Calling Code", value=f"+{data.calling_code}")
        if (lat := data.latitude) and (lon := data.longitude):
            maps_link = f"[{data.co_ordinates}](https://www.google.com/maps?q={lat},{lon})"
            embed.add_field(name="Latitude & Longitude", value=maps_link)
        if len(embed.fields) == 5:
            embed.add_field(name='\u200b', value='\u200b')
        if data.threat.blocklists:
            embed.add_field(
                name=f"In {len(data.threat.blocklists)} Blocklists",
                value=", ".join(str(b) for b in data.threat.blocklists),
                inline=False,
            )
        return embed

    @commands.is_owner()
    @commands.command(name="ip")
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def ipinfo(self, ctx: commands.Context, *, ip_address: str):
        """Fetch basic geolocation data on a public IPv4 address.

        **Usage:** `[p]ip <ip_address>`

        You can bulk query info on upto 20 IPv4 addresses at once.
        For this, simply provide IP addresses separated by space.
        Only max. 20 IPs will be processed at once to avoid API ratelimits.

        **Example:**
            - `[p]ip 136.23.11.195`
            - `[p]ip 117.111.1.112 183.157.171.217 62.171.168.2 107.189.14.180`
        """
        api_key = (await ctx.bot.get_shared_api_tokens("ipdata")).get("api_key")
        async with ctx.typing():
            ip_addrs = ip_address.split(" ")
            if len(ip_addrs) == 1:
                data = await IPData.request(self.session, ip_address, api_key)
                if data.message:
                    return await ctx.send(str(data.message))
                assert isinstance(data, IPData)
                embed = self._make_embed(data, await ctx.embed_colour())
                if ctx.author.id == 306810730055729152:
                    embed.add_field(
                        name='API Quota', value=f"{data.count}/1500 used today", inline=False
                    )
                await ctx.send(embed=embed)
                return

            embeds = []
            for i, ip_addr in enumerate(ip_addrs[:20], 1):
                data = await IPData.request(self.session, ip_addr, api_key)
                if error_msg := data.message:
                    embed = discord.Embed(colour=await ctx.embed_colour(), description=error_msg)
                    if str(error_msg).startswith("http"):
                        embed.set_image(url=error_msg)
                else:
                    embed = self._make_embed(data, await ctx.embed_colour())
                    embed.set_footer(text=f"Page {i} of {len(ip_addrs)}")
                if ctx.author.id == 306810730055729152:
                    embed.add_field(
                        name='API Quota', value=f"{data.count}/1500 used today", inline=False
                    )
                embeds.append(embed)

            if not embeds:
                return await ctx.send("Sad trombone. No results. 😔")

        await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=90.0)
