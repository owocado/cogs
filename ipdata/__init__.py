from discord.utils import maybe_coroutine

from .ipdata import IPData

__red_end_user_data_statement__ = "This cog does not persistently store data or metadata about users."


async def setup(bot):
    await maybe_coroutine(bot.add_cog, IPData(bot))
