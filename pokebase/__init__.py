from discord.utils import maybe_coroutine

from .pokebase import Pokebase

__red_end_user_data_statement__ = "This cog does not persistently store data about users."


async def setup(bot):
    await maybe_coroutine(bot.add_cog, Pokebase())
