from .ocr import OCR

__red_end_user_data_statement__ = "This cog does not persistently store any data or metadata about users."


def setup(bot):
    bot.add_cog(OCR(bot))
