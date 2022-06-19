from redbot.core.bot import Red

from .jsk_cog import Jishaku


async def setup(bot: Red):
    await bot.add_cog(Jishaku(bot=bot))
