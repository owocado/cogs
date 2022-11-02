import asyncio
from typing import cast

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .models import IPData, IPInfoIO
from .utils import make_embed, query_ipinfo


class IP(commands.Cog):
    """Get basic geolocation info on a public IP address."""

    __authors__ = ["ow0x"]
    __version__ = "3.0.0"

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
                ipinfo_result = await query_ipinfo(self.session, ip_address)
                ipinfo_data = (
                    IPInfoIO.from_data(ipinfo_result["data"])
                    if "data" in ipinfo_result else None
                )
                if data.message:
                    await ctx.send(str(data.message))
                    return
                data = cast(IPData, data)
                embed = make_embed(await ctx.embed_colour(), data, ipinfo_data)
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
                    embed = make_embed(await ctx.embed_colour(), data)
                    embed.set_footer(text=f"Page {i} of {len(ip_addrs)}")
                if ctx.author.id == 306810730055729152:
                    embed.add_field(
                        name='API Quota',
                        value=f"{data.count}/1500 used today",
                        inline=False
                    )
                embeds.append(embed)

            if not embeds:
                await ctx.send("Sad trombone. No results. 😔")
                return

        await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=90.0)
