from discord.utils import maybe_coroutine

from .core import Anilist


async def setup(bot):
    await maybe_coroutine(bot.add_cog, Anilist())
