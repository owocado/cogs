import asyncio
from io import BytesIO

import aiohttp
from PIL import Image, ImageDraw, ImageFont
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path


class WhosThatPokemon(commands.Cog):
    """Guess a game of Who's that Pokémon!"""

    __author__ = "ow0x, dragonfire535"
    __version__ = "0.0.1"


    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    async def whosthatpokemon(self, ctx: commands.Context):
        """Guess a game of Who's that Pokémon!"""
        await ctx.send("Fire nation attcks!")
