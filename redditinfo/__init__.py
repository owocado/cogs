from .redditinfo import RedditInfo

__red_end_user_data_statement__ = "This cog does not persistently store data about users."


def setup(bot):
    n = RedditInfo(bot)
    bot.add_cog(n)
