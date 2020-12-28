from redbot.core.bot import Red

from .roleplay import Roleplay


async def setup(bot: Red):
    n = Roleplay(bot)
    bot.add_cog(n)
