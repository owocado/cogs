import jishaku
from jishaku.cog import OPTIONAL_FEATURES, STANDARD_FEATURES

from redbot.core import commands

jishaku.Flags.RETAIN = True
jishaku.Flags.NO_UNDERSCORE = True
jishaku.Flags.FORCE_PAGINATOR = True
jishaku.Flags.NO_DM_TRACEBACK = True


class Jishaku(*STANDARD_FEATURES, *OPTIONAL_FEATURES):
    """Jishaku, a debugging and testing cog for discord.py rewrite bots."""

    __authors__ = ["Gorialis", "ow0x"]
    __version__ = "2.5.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:  # Thanks Sinbad!
        authors = map(lambda x: f'[{x}](https://github.com/{x})', self.__authors__)
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(authors)}\n"
            f"**Cog version:**  v{self.__version__}"
        )
