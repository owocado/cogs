from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES


class Jishaku(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    """Jishaku, a debugging and testing cog for discord.py rewrite bots."""
    pass

    __version__ = "2.3.0"
    __author__ = "Gorialis"

    def format_help_for_context(self, ctx):
        """Thanks Sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\nAuthor: {self.__author__}\nCog Version: {self.__version__}"
