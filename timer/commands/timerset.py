from abc import ABC

from redbot.core import checks, commands

from ..abc import CompositeMetaClass, MixinMeta
from ..pcx_lib import SettingDisplay, checkmark


class TimerSetCommands(MixinMeta, ABC, metaclass=CompositeMetaClass):
    @commands.group()
    @checks.admin_or_permissions(manage_guild=True)
    async def timerset(self, ctx: commands.Context):
        """Manage Timers settings."""
        pass

    @timerset.command()
    async def settings(self, ctx: commands.Context):
        """Display current settings."""
        server_section = SettingDisplay("Server Settings")
        if ctx.guild:
            server_section.add(
                "Me too",
                "Enabled"
                if await self.config.guild(ctx.guild).me_too()
                else "Disabled",
            )

        if await ctx.bot.is_owner(ctx.author):
            global_section = SettingDisplay("Global Settings")
            global_section.add(
                "Maximum timers per user", await self.config.max_user_timers()
            )

            timers = [
                timer["REPEAT"] if "REPEAT" in timer else None
                for timer in await self.config.timers()
            ]
            pending_timers_message = f"{len(timers)}"
            if timers:
                repeating_timers = [repeat for repeat in timers if repeat]
                if repeating_timers:
                    pending_timers_message += (
                        f" ({len(repeating_timers)} " +
                        f"{'is' if len(repeating_timers) == 1 else 'are'} repeating)"
                    )
            stats_section = SettingDisplay("Stats")
            stats_section.add(
                "Pending timers",
                pending_timers_message,
            )
            stats_section.add("Total timers sent", await self.config.total_sent())

            await ctx.send(server_section.display(global_section, stats_section))

        else:
            await ctx.send(str(server_section))

    @timerset.command()
    @commands.guild_only()
    async def metoo(self, ctx: commands.Context):
        """Toggle the bot asking if others want to be reminded in this server.

        If the bot doesn't have the Add Reactions permission in the channel, it won't ask regardless.
        """
        me_too = not await self.config.guild(ctx.guild).me_too()
        await self.config.guild(ctx.guild).me_too.set(me_too)
        await ctx.send(
            checkmark(
                f"I will {'now' if me_too else 'no longer'} ask if others want to be reminded of the timer."
            )
        )

    @timerset.command()
    @checks.is_owner()
    async def max(self, ctx: commands.Context, maximum: int):
        """Global: Set the maximum number of timers a user can create at one time."""
        await self.config.max_user_timers.set(maximum)
        await ctx.send(
            checkmark(
                f"Maximum timers per user is now set to {await self.config.max_user_timers()}"
            )
        )
