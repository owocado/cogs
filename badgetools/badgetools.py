from collections import Counter

# Required by Red
import discord
from redbot.core import checks, commands
from redbot.core.bot import Red
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

class BadgeTools(commands.Cog):
    """Various commands to show the stats about users' profile badges."""

    __author__ = ["siu3334", "<@306810730055729152>", "Fixator10"]
    __version__ = "0.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nCog Version: {self.__version__}"

    def __init__(self, bot: Red):
        self.bot = bot
        self.emojis = self.bot.loop.create_task(self.init())
        self.valid = [
            "staff",
            "partner",
            "hypesquad",
            "bug_hunter",
            "hypesquad_bravery",
            "hypesquad_brilliance",
            "hypesquad_balance",
            "early_supporter",
            "team_user",
            "system",
            "bug_hunter_level_2",
            "verified_bot",
            "verified_bot_developer",
        ]

    def cog_unload(self):
        if self.emojis:
            self.emojis.cancel()

    # Credits to flaree (taken from https://github.com/flaree/Flare-Cogs/blob/master/userinfo/userinfo.py#L33)
    # Thanks flare <3
    async def init(self):
        await self.bot.wait_until_ready()
        self.badge_emojis = {
            "staff": discord.utils.get(self.bot.emojis, id=790550232387289088),
            "early_supporter": discord.utils.get(self.bot.emojis, id=706198530837970998),
            "hypesquad_balance": discord.utils.get(self.bot.emojis, id=706198531538550886),
            "hypesquad_bravery": discord.utils.get(self.bot.emojis, id=706198532998299779),
            "hypesquad_brilliance": discord.utils.get(self.bot.emojis, id=706198535846101092),
            "hypesquad": discord.utils.get(self.bot.emojis, id=706198537049866261),
            "verified_bot_developer": discord.utils.get(self.bot.emojis, id=706198727953612901),
            "bug_hunter": discord.utils.get(self.bot.emojis, id=749067110847742062),
            "bug_hunter_level_2": discord.utils.get(self.bot.emojis, id=706199712402898985),
            "partner": discord.utils.get(self.bot.emojis, id=748668634871889930),
            "verified_bot": discord.utils.get(self.bot.emojis, id=710561078488334368),
        }

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def badgecount(self, ctx: commands.Context):
        """Shows the summary of badgecount of the server."""
        guild = ctx.guild

        count = Counter()
        # Credits to Fixator10 for improving this snippet
        # Thanks Fixator <3
        async for usr in AsyncIter(guild.members):
            async for flag in AsyncIter(usr.public_flags.all()):
                count[flag.name] += 1

        msg = ""
        pad = len(str(len(ctx.guild.members)))
        for k, v in sorted(count.items()):
            msg += f"{self.badge_emojis[k]} `{str(v).zfill(pad)}` : {k.replace('_', ' ').title()}\n"

        e = discord.Embed(colour=await ctx.embed_color())
        e.set_footer(text=f"For Guild: {guild.name}", icon_url=str(guild.icon_url))
        e.add_field(name="Badge Count:", value=msg)
        await ctx.send(embed=e)
