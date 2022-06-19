from discord.utils import maybe_coroutine
from redbot.core.bot import Red

from .moviedb import MovieDB

__red_end_user_data_statement__ = "This cog does not persistently store data about users."


async def setup(bot: Red):
    await maybe_coroutine(bot.add_cog, MovieDB())
