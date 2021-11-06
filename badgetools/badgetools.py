from collections import Counter
from datetime import datetime, timezone

import discord
from dateutil import relativedelta
from redbot.core import commands
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import close_menu, menu, DEFAULT_CONTROLS


class BadgeTools(commands.Cog):
    """Various commands to show the stats about users' profile badges."""

    __author__ = ["ow0x", "Fixator10"]
    __version__ = "0.1.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot

    def badge_emoji(self, badge_name: str):
        cog = self.bot.get_cog("Userinfo")
        if cog is None:
            return f"{badge_name.replace('_', ' ').title()} :"
        emoji = str(cog.badge_emojis[badge_name])
        if "848561838974697532" in str(emoji):
            emoji = "<:verified_bot:848557763328344064>"
        return emoji

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def badgecount(self, ctx: commands.Context):
        """Shows the count of user profile badges of the server."""
        guild = ctx.guild

        async with ctx.typing():
            count = Counter()
            # Credits to Fixator10 for improving this snippet
            # Thanks Fixator <3
            async for user in AsyncIter(guild.members):
                async for flag in AsyncIter(user.public_flags.all()):
                    count[flag.name] += 1

            message = ""
            fill = len(str(len(guild.members))) - 1
            for k, v in sorted(count.items(), key=lambda x: x[1], reverse=True):
                message += f"**{self.badge_emoji(k)}\u2000`{str(v).zfill(fill)}`**\n"

            embed = discord.Embed(colour=await ctx.embed_color())
            embed.set_author(name=str(guild.name), icon_url=str(guild.icon_url))
            embed.description = message

        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    @commands.guild_only()
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def hasbadge(self, ctx: commands.Context, *, badge: str):
        """Returns the list of users with X profile badge in the server."""
        badge = badge.replace(" ", "_").lower()

        valid_flags = list(discord.PublicUserFlags.VALID_FLAGS.keys())
        inform = "`{}` badge not found! It needs to be one of:\n\n{}".format(
            badge, "\n".join([f"> `{x}`" for x in valid_flags])
        )
        if badge not in valid_flags:
            return await ctx.send(inform)

        list_of = []
        # Thanks Fixator <3
        async for user in AsyncIter(sorted(ctx.guild.members, key=lambda x: x.joined_at)):
            async for flag in AsyncIter(user.public_flags.all()):
                if flag.name == badge:
                    list_of.append(f"str(user)")

        output = "\n".join(list_of)

        embed_list = []
        for page in pagify(output, ["\n"], page_length=1000):
            em = discord.Embed(colour=await ctx.embed_color())
            em.set_author(name=str(ctx.guild.name), icon_url=str(ctx.guild.icon_url))
            em.description = page
            footer = f"Found {len(list_of)} users with {badge.replace('_', ' ').title()} badge!"
            em.set_footer(text=footer)
            embed_list.append(em)

        if not embed_list:
            return await ctx.send(f"I could not find any users with `{badge}` badge.")

        controls = {"❌": close_menu} if len(embed_list) == 1 else DEFAULT_CONTROLS
        await menu(ctx, embed_list, controls=controls, timeout=60.0)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def boosters(self, ctx: commands.Context):
        """Returns the list of active boosters of the server."""
        guild = ctx.guild

        if not guild.premium_subscribers:
            return await ctx.send(f"{guild.name} does not have any boost(er)s yet.")

        b_list = "`[since {since:>9}]`  {user_name_tag}"
        all_boosters = [
            b_list.format(
                since=self._relative_timedelta(user.premium_since),
                user_name_tag=str(user),
            )
            for user in sorted(guild.premium_subscribers, key=lambda x: x.premium_since)
        ]
        output = "\n".join(all_boosters)
        footer = f"{guild.premium_subscription_count} boosts from {len(guild.premium_subscribers)} boosters!"

        embed_list = []
        for page in pagify(output, ["\n"], page_length=1500):
            em = discord.Embed(colour=await ctx.embed_color())
            em.description = page
            em.set_footer(text=footer)
            embed_list.append(em)

        controls = {"❌": close_menu} if len(embed_list) == 1 else DEFAULT_CONTROLS
        await menu(ctx, embed_list, controls=controls, timeout=60.0)

    @staticmethod
    def _relative_timedelta(date_time):
        dt1 = datetime.now(timezone.utc).replace(tzinfo=None)

        diff = relativedelta.relativedelta(dt1, date_time)

        yrs, mths, days = (diff.years, diff.months, diff.days)
        hrs, mins, secs = (diff.hours, diff.minutes, diff.seconds)

        pretty = f"{yrs}y {mths}mo {days}d {hrs}h {mins}m {secs}s"
        to_join = " ".join([x for x in pretty.split() if x[0] != "0"][:2])

        return to_join
