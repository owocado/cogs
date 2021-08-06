# Credits to Fixator10 for this logic <3
from asyncio import create_task

from .userinfo import Userinfo

__red_end_user_data_statement__ = "This cog does not persistently store any PII data about users."


async def setup_after_ready(bot):
    await bot.wait_until_red_ready()
    cog = Userinfo(bot)
    for name, command in cog.all_commands.items():
        if not command.parent:
            if bot.get_command(name):
                command.name = f"u{command.name}"
    bot.add_cog(cog)

def setup(bot):
    create_task(setup_after_ready(bot))
