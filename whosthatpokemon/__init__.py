from redbot.core.bot import Red

from .main import WhosThatPokemon


def setup(bot: Red):
	bot.add_cog(WhosThatPokemon(bot))
