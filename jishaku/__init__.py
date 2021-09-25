from redbot.core import commands

from .jishaku import Jishaku


def setup(bot: commands.Bot):
    bot.add_cog(Jishaku(bot=bot))
