from .phonefinder import PhoneFinder

__red_end_user_data_statement__ = "This cog does not store any PII data or metadata about users."


def setup(bot):
	cog = PhoneFinder(bot)
	bot.add_cog(cog)
