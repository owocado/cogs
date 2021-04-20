from redbot.core.bot import Red

from .steamcog import SteamCog

__red_end_user_data_statement__ = "This cog does not persistently store data about users."


async def setup(bot: Red):
    n = SteamCog(bot)
    bot.add_cog(n)
