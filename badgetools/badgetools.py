import datetime

from collections import Counter
from dateutil import relativedelta

# Required by Red
import discord
from redbot.core import commands
from redbot.core.commands import GuildConverter
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import inline, pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS


class BadgeTools(commands.Cog):
    """Various commands to show the stats about users' profile badges."""

    __author__ = ["siu3334", "Fixator10"]
    __version__ = "0.0.6"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nCog Version: {self.__version__}"

    def __init__(self, bot):
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
        self.status_emojis = {
            "mobile": discord.utils.get(self.bot.emojis, id=749067110931759185),
            "online": discord.utils.get(self.bot.emojis, id=749221433552404581),
            "away": discord.utils.get(self.bot.emojis, id=749221433095356417),
            "dnd": discord.utils.get(self.bot.emojis, id=749221432772395140),
            "offline": discord.utils.get(self.bot.emojis, id=749221433049088082),
            "streaming": discord.utils.get(self.bot.emojis, id=749221434039205909),
        }
        self.badge_emojis = {
            "staff": discord.utils.get(self.bot.emojis, id=848556248832016384),
            "early_supporter": discord.utils.get(self.bot.emojis, id=706198530837970998),
            "hypesquad_balance": discord.utils.get(self.bot.emojis, id=706198531538550886),
            "hypesquad_bravery": discord.utils.get(self.bot.emojis, id=706198532998299779),
            "hypesquad_brilliance": discord.utils.get(self.bot.emojis, id=706198535846101092),
            "hypesquad": discord.utils.get(self.bot.emojis, id=706198537049866261),
            "verified_bot_developer": discord.utils.get(self.bot.emojis, id=706198727953612901),
            "bug_hunter": discord.utils.get(self.bot.emojis, id=848556247632052225),
            "bug_hunter_level_2": discord.utils.get(self.bot.emojis, id=706199712402898985),
            "partner": discord.utils.get(self.bot.emojis, id=848556249192202247),
            "verified_bot": discord.utils.get(self.bot.emojis, id=848557763328344064),
            "discord_certified_moderator": discord.utils.get(self.bot.emojis, id=848556248357273620),
        }

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def badgecount(self, ctx: commands.Context, guild: GuildConverter = None):
        """Shows the summary of badgecount of the server."""
        guild = guild or ctx.guild

        count = Counter()
        # Credits to Fixator10 for improving this snippet
        # Thanks Fixator <3
        async for user in AsyncIter(guild.members):
            async for flag in AsyncIter(user.public_flags.all()):
                count[flag.name] += 1

        msg = ""
        pad = len(str(len(guild.members))) - 1
        for k, v in sorted(count.items()):
            msg += f"{self.badge_emojis[k]} `{str(v).zfill(pad)}` : {k.replace('_', ' ').title()}\n"

        e = discord.Embed(colour=await ctx.embed_color())
        e.set_footer(text=f"For Guild: {guild.name}", icon_url=str(guild.icon_url))
        e.add_field(name="Badge Count:", value=msg)
        await ctx.send(embed=e)

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def inbadge(self, ctx: commands.Context, badge: str, guild: GuildConverter = None):
        """Returns the list of users with X profile badge in the server."""

        guild = guild or ctx.guild

        badgeslist = ", ".join(inline(m) for m in self.valid)
        warn = f"Provided `badge` name is not valid! It needs to be either of:\n\n{badgeslist}"

        if badge.lower() not in self.valid:
            return await ctx.send(warn)

        list_of = []
        # Thanks Fixator <3
        async for user in AsyncIter(sorted(guild.members, key=lambda x: x.joined_at)):
            async for flag in AsyncIter(user.public_flags.all()):
                if flag.name == badge:
                    list_of.append(
                        "{status}  {user_name_tag}\n".format(
                            status=f"{self.status_emojis['mobile']}"
                            if user.is_on_mobile()
                            else f"{self.status_emojis['streaming']}"
                            if any(
                                a.type is discord.ActivityType.streaming
                                for a in user.activities
                            )
                            else f"{self.status_emojis['online']}"
                            if user.status.name == "online"
                            else f"{self.status_emojis['offline']}"
                            if user.status.name == "offline"
                            else f"{self.status_emojis['dnd']}"
                            if user.status.name == "dnd"
                            else f"{self.status_emojis['away']}",
                            user_name_tag=str(user),
                        )
                    )
        output = "".join(m for m in list_of)
        total = len([m for m in list_of])

        embed_list = []
        for page in pagify(output, ["\n"], page_length=1000):
            em = discord.Embed(colour=await ctx.embed_color())
            em.set_author(name=str(guild.name), icon_url=str(guild.icon_url))
            em.description = page
            em.set_footer(text=f"Found {total} users with {badge.replace('_', ' ').title()} badge!")
            embed_list.append(em)
        if not embed_list:
            return await ctx.send("I couldn't find any users with `{badge}` badge.")
        elif len(embed_list) == 1:
            return await ctx.send(embed=embed_list[0])
        else:
            await menu(ctx, embed_list, DEFAULT_CONTROLS, timeout=60.0)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def boosters(self, ctx: commands.Context, guild: GuildConverter = None):
        """Returns the list of active boosters of the server."""

        guild = guild or ctx.guild
        if guild.premium_subscription_count == 0:
            return await ctx.send(f"`{guild.name}` server doesn't have any boost(er)s yet.")

        b_list = "{status}  `[since ~{since:>9}]`  {user_name_tag}"
        all_boosters = [
            b_list.format(
                status=f"{self.status_emojis['mobile']}"
                if user.is_on_mobile()
                else f"{self.status_emojis['streaming']}"
                if any(
                    a.type is discord.ActivityType.streaming
                    for a in user.activities
                )
                else f"{self.status_emojis['online']}"
                if user.status.name == "online"
                else f"{self.status_emojis['offline']}"
                if user.status.name == "offline"
                else f"{self.status_emojis['dnd']}"
                if user.status.name == "dnd"
                else f"{self.status_emojis['away']}",
                user_name_tag=str(user),
                since=self._relative_timedelta(user.premium_since),
            )
            for user in sorted(guild.premium_subscribers, key=lambda x: x.premium_since)
        ]
        output = "\n".join(all_boosters)
        footer = (
            f"{guild.name} currently has {guild.premium_subscription_count} boosts "
            + f"thanks to these {len(guild.premium_subscribers)} boosters! ❤️"
        )

        embed_list = []
        for page in pagify(output, ["\n"], page_length=1500):
            em = discord.Embed(colour=await ctx.embed_color())
            em.description = page
            em.set_footer(text=footer)
            embed_list.append(em)

        if len(embed_list) == 1:
            return await ctx.send(embed=embed_list[0])
        else:
            await menu(ctx, embed_list, DEFAULT_CONTROLS, timeout=60.0)

    @staticmethod
    def _relative_timedelta(date_time):
        dt1 = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        dt2 = date_time

        diff = relativedelta.relativedelta(dt1, dt2)

        yrs, mths, days = (diff.years, diff.months, diff.days)
        hrs, mins, secs = (diff.hours, diff.minutes, diff.seconds)

        pretty = f"{yrs}y {mths}mth {days}d {hrs}h {mins}m {secs}s"
        to_join = " ".join([x for x in pretty.split() if x[0] != '0'][:2])

        return to_join
