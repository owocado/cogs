from redbot.core.bot import Red

from .badgetools import BadgeTools


async def setup(bot: Red):
    n = BadgeTools(bot)
    bot.add_cog(n)
