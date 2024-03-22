from redbot.core.errors import CogLoadError

from .ocr import OCR

__red_end_user_data_statement__ = (
    "This cog does not persistently store any data or metadata about users."
)


async def setup(bot):
    if not getattr(bot, "session", None):
        raise CogLoadError("This cog requires bot.session attr to be set.")
    await bot.add_cog(OCR(bot))

