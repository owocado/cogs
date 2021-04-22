from .vision import Vision

__red_end_user_data_statement__ = "This cog does not persistently store data about users."


def setup(bot):
    n = Vision(bot)
    bot.add_cog(n)
