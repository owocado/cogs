from discord.utils import maybe_coroutine

from .kickstarter import Kickstarter

__red_end_user_data_statement__ = "This cog does not persistently store any PII data about users."


async def setup(bot):
    await maybe_coroutine(bot.add_cog, Kickstarter())
