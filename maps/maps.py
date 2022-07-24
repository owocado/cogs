import aiohttp
import asyncio

from io import BytesIO
from typing import Optional

import discord
from redbot.core import commands

MAP_TYPES = ["roadmap", "satellite", "terrain", "hybrid"]


class Maps(commands.Cog):
    """Fetch a Google map of a specific location."""

    __authors__ = ["ow0x"]
    __version__ = "1.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"Authors:  {', '.join(self.__authors__)}\n"
            f"Cog version:  v{self.__version__}"
        )

    @commands.command()
    @commands.is_owner()
    @commands.bot_has_permissions(attach_files=True)
    async def map(
        self,
        ctx: commands.Context,
        zoom: Optional[int],
        map_type: str,
        *,
        location: str
    ):
        """Fetch a Google map of a specific location in various modes.

        `zoom` parameter accepts values from 1 to 20. Defaults to 12 if any other value is provided.

        Zoom levels to show the approximate level of detail:
        ```
        1  : World
        5  : Landmass/continent
        10 : City
        15 : Streets
        20 : Buildings
        ```

        `map_type` parameter accepts only below 4 values:
        ```
        roadmap, satellite, terrain, hybrid
        ```
        You can read more on that in detail on Google Developers docs:
        https://developers.google.com/maps/documentation/maps-static/start#MapTypes
        """
        api_key = (await ctx.bot.get_shared_api_tokens("googlemaps")).get("api_key")
        if not api_key:
            await ctx.send("\u26d4 API key not set. Ask bot owner to set it first!")
            return
        if map_type not in MAP_TYPES:
            return await ctx.send_help()

        zoom = zoom if (zoom and 1 <= zoom <= 20) else 12
        # maptype = "roadmap" if maptype not in MAP_TYPES else maptype

        async with ctx.typing():
            base_url = "https://maps.googleapis.com/maps/api/staticmap"
            params = {
                "zoom": zoom,
                "size": "600x600",
                "scale": "2",
                "maptype": map_type,
                "center": location,
                "key": api_key
            }
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(base_url, params=params) as response:
                        if response.status != 200:
                            await ctx.send(f"https://http.cat/{response.status}")
                            return
                        image = BytesIO(await response.read())
                        image.seek(0)
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            url = f"<https://www.google.com/maps/search/{location.replace(' ', '+')}>"
            return await ctx.send(content=url, file=discord.File(image, "map.png"))
