from .stackoverflow import StackOverflow

__red_end_user_data_statement__ = "This cog does not persistently store data about users."


def setup(bot):
    n = StackOverflow(bot)
    bot.add_cog(n)
