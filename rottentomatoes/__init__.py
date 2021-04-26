from .rtomato import RottenTomatoes

__red_end_user_data_statement__ = "This cog does not persistently store data about users."


async def setup(bot):
    n = RottenTomatoes(bot)
    bot.add_cog(n)
