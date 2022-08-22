from .core import Anilist


async def setup(bot):
    await bot.add_cog(Anilist())
