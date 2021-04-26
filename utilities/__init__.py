from .utilities import Utilities

__red_end_user_data_statement__ = "This cog does not persistently store data about users."


async def setup(bot):
    n = MovieDB(bot)
    bot.add_cog(n)
