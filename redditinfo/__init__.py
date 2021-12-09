from .redditinfo import RedditInfo

__red_end_user_data_statement__ = "This cog does not persistently store any PII data or metadata about users."


async def setup(bot):
    cog = RedditInfo(bot)
    await cog.initialize()
    bot.add_cog(cog)
