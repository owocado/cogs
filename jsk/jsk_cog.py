import jishaku
from jishaku.cog import OPTIONAL_FEATURES, STANDARD_FEATURES

jishaku.Flags.RETAIN = True
jishaku.Flags.NO_UNDERSCORE = True
jishaku.Flags.FORCE_PAGINATOR = True
jishaku.Flags.NO_DM_TRACEBACK = True


class Jishaku(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    """Jishaku, a debugging and testing cog for discord.py rewrite bots."""


    __author__, __version__ = ("Author: Gorialis", "Cog Version: 2.3.2")

    def format_help_for_context(self, ctx):
        """Thanks Sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n{self.__author__}\n{self.__version__}"
