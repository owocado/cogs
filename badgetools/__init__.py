from .badgetools import BadgeTools

__red_end_user_data_statement__ = "This cog does not persistently store data or metadata about users."


async def setup(bot):
    n = BadgeTools(bot)
    bot.add_cog(n)
