import aiohttp
import asyncio

import discord
from redbot.core import commands


class Pokebase(commands.Cog):
    """Search for various info about a Pokémon and related data."""

    __author__ = ["phalt", "siu3334 (<@306810730055729152>)"]
    __version__ = "0.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())
