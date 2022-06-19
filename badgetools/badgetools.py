from collections import Counter
from datetime import datetime, timezone

import discord
from dateutil import relativedelta
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import close_menu, menu, DEFAULT_CONTROLS


class BadgeTools(commands.Cog):
    """Various commands to show the stats about users' profile badges."""

    __authors__ = ["ow0x"]
    __version__ = "1.0.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"Authors:  {', '.join(self.__authors__)}\n"
            f"Cog version:  v{self.__version__}"
        )

    def badge_emoji(self, ctx, badge_name: str):
        cog = ctx.bot.get_cog("Userinfo")
        if cog is None:
            return f"{badge_name.replace('_', ' ').title()} :"
        emoji = str(cog.badge_emojis.get(badge_name))
        if "848561838974697532" in emoji:
            emoji = "<:verified_bot:848557763328344064>"
        return emoji

    def statusmoji(self, ctx, member: discord.Member):
        cog = ctx.bot.get_cog("Userinfo")
        if cog is None:
            return ""
        if member.is_on_mobile():
            return f"{cog.status_emojis.get('mobile', '📱')}  "
        elif member.status.name == "online":
            return f"{cog.status_emojis.get('online', '🟢')}  "
        elif member.status.name == "idle":
            return f"{cog.status_emojis.get('idle', '🟠')}  "
        elif member.status.name == "dnd":
            return f"{cog.status_emojis.get('dnd', '🔴')}  "
        elif any(a.type is discord.ActivityType.streaming for a in member.activities):
            return f"{cog.status_emojis.get('streaming', '🟣')}  "
        else:
            return f"{cog.status_emojis.get('offline', '⚫')}  "

    @staticmethod
    def _icon(guild: discord.Guild) -> str:
        if int(discord.__version__[0]) >= 2:
            return guild.icon.url if guild.icon else ""
        return guild.icon_url or ""

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def badgecount(self, ctx: commands.Context):
        """Shows the count of user profile badges of the server."""
        async with ctx.typing():
            count = Counter()
            # Credits to Fixator10 for improving this snippet
            # Thanks Fixator <3
            async for user in AsyncIter(ctx.guild.members):
                async for flag in AsyncIter(user.public_flags.all()):
                    count[flag.name] += 1

            fill = len(str(ctx.guild.member_count)) - 1
            message = "\n".join(
                f"**{self.badge_emoji(ctx, k)}\u2000`{str(v).zfill(fill)}`**"
                for k, v in sorted(count.items(), key=lambda x: x[1], reverse=True)
            )
            embed = discord.Embed(colour=await ctx.embed_color())
            embed.set_author(name=str(ctx.guild), icon_url=self._icon(ctx.guild))
            embed.description = message

        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(hidden=True)
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def hasbadge(self, ctx: commands.Context, *, badge: str):
        """Returns the list of users with X profile badge in the server."""
        badge = badge.replace(" ", "_").lower()
        valid_flags = "\n".join([f"> `{x}`" for x in list(discord.PublicUserFlags.VALID_FLAGS.keys())])
        if badge not in valid_flags:
            inform = f"`{badge}` badge not found! It needs to be one of:\n\n{valid_flags}"
            return await ctx.send(inform)

        list_of = []
        # Thanks Fixator <3
        async for user in AsyncIter(sorted(ctx.guild.members, key=lambda x: x.joined_at)):
            async for flag in AsyncIter(user.public_flags.all()):
                if flag.name == badge:
                    list_of.append(f"{self.statusmoji(ctx, user)}{user}")

        output = "\n".join(list_of)
        pages = []
        for page in pagify(output, ["\n"], page_length=1000):
            em = discord.Embed(colour=await ctx.embed_color(), description=page)
            em.set_author(name=str(ctx.guild), icon_url=self._icon(ctx.guild))
            footer = f"Found {len(list_of)} users with {badge.replace('_', ' ').title()} badge!"
            em.set_footer(text=footer)
            pages.append(em)

        if not pages:
            return await ctx.send(f"I could not find any users with `{badge}` badge.")
        controls = {"❌": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=60.0)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def boosters(self, ctx: commands.Context):
        """Returns the list of active boosters of the server."""
        if not ctx.guild.premium_subscribers:
            return await ctx.send(f"{ctx.guild} does not have any boost(er)s yet.")

        output = "\n".join(
            f"{self.statusmoji(ctx, user)}`[since {self._parse_time(user.premium_since):>9}]`  {user}"
            for user in sorted(ctx.guild.premium_subscribers, key=lambda x: x.premium_since)
        )
        boosts, boosters = (ctx.guild.premium_subscription_count, len(ctx.guild.premium_subscribers))
        pages = []
        for page in pagify(output, ["\n"], page_length=1500):
            em = discord.Embed(colour=await ctx.embed_color(), description=page)
            em.set_author(name=str(ctx.guild), icon_url=self._icon(ctx.guild))
            em.set_footer(text=f"{boosts} boosts  •  {boosters} boosters!")
            pages.append(em)

        controls = {"❌": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=60.0)

    @staticmethod
    def _parse_time(date_time):
        dt1 = datetime.now(timezone.utc).replace(tzinfo=None)
        diff = relativedelta.relativedelta(dt1, date_time)

        yrs, mths, days = (diff.years, diff.months, diff.days)
        hrs, mins, secs = (diff.hours, diff.minutes, diff.seconds)
        pretty = f"{yrs}y {mths}mo {days}d {hrs}h {mins}m {secs}s"
        return " ".join([x for x in pretty.split() if x[0] != "0"][:2])
