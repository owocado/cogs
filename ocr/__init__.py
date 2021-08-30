from .ocr import OCR

__red_end_user_data_statement__ = "This cog does not persistently store data about users."


def setup(bot):
    n = OCR()
    bot.add_cog(n)
