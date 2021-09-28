from redbot.core import commands

from .jsk_cog import Jishaku


def setup(bot: commands.Bot):
    bot.add_cog(Jishaku(bot=bot))
