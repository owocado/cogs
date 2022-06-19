from discord.utils import maybe_coroutine

from .redditinfo import RedditInfo

__red_end_user_data_statement__ = "This cog does not persistently store any PII data or metadata about users."


async def setup(bot):
    cog = RedditInfo(bot)
    await maybe_coroutine(bot.add_cog, cog)
    await cog.initialize()
