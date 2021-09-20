"""Timer cog for Red-DiscordBot ported and enhanced by PhasecoreX."""
import asyncio
import logging
import time as current_time

import discord
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import humanize_timedelta as htd

from .abc import CompositeMetaClass
from .commands import Commands

__author__ = "PhasecoreX"
log = logging.getLogger("red.pcxcogs.timer")


class Timer(Commands, commands.Cog, metaclass=CompositeMetaClass):
    """Set a timer to remind you of something in a channel instead of in DMs."""

    default_global_settings = {
        "schema_version": 0,
        "total_sent": 0,
        "max_user_timers": 20,
        "timers": [],
    }
    default_guild_settings = {
        "me_too": False,
    }
    SEND_DELAY_SECONDS = 30

    def __init__(self, bot):
        """Set up the cog."""
        super().__init__()
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1224444860, force_registration=True
        )
        self.config.register_global(**self.default_global_settings)
        self.config.register_guild(**self.default_guild_settings)
        self.bg_loop_task = None
        self.me_too_timers = {}
        self.timer_emoji = "\N{ALARM CLOCK}"

    async def initialize(self):
        """Perform setup actions before loading cog."""
        await self._migrate_config()
        self._enable_bg_loop()

    async def _migrate_config(self):
        """Perform some configuration migrations."""
        if not await self.config.schema_version():
            # Add/generate USER_TIMER_ID, rename some fields
            current_timers = await self.config.timers()
            new_timers = []
            user_timer_ids = {}
            for timer in current_timers:
                user_timer_id = user_timer_ids.get(timer["ID"], 1)
                new_timer = {
                    "USER_TIMER_ID": user_timer_id,
                    "USER_ID": timer["ID"],
                    "TIMER": timer["TEXT"],
                    "FUTURE": timer["FUTURE"],
                    "FUTURE_TEXT": timer["FUTURE_TEXT"],
                    "JUMP_LINK": None,
                }
                user_timer_ids[timer["ID"]] = user_timer_id + 1
                new_timers.append(new_timer)
            await self.config.timers.set(new_timers)
            await self.config.schema_version.set(1)

    def _enable_bg_loop(self):
        """Set up the background loop task."""
        self.bg_loop_task = self.bot.loop.create_task(self.bg_loop())

        def error_handler(fut: asyncio.Future):
            try:
                fut.result()
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                log.exception(
                    "Unexpected exception occurred in background loop of Timer: ",
                    exc_info=exc,
                )
                asyncio.create_task(
                    self.bot.send_to_owners(
                        "An unexpected exception occurred in the background loop of Timer.\n"
                        + "Timers will not be sent out until the cog is reloaded.\n" +
                        "Check your console or logs for details or any errors."
                    )
                )

        self.bg_loop_task.add_done_callback(error_handler)

    def cog_unload(self):
        """Clean up when cog shuts down."""
        if self.bg_loop_task:
            self.bg_loop_task.cancel()

    async def red_delete_data_for_user(self, *, requester, user_id: int):
        """There's already a [p]ftimers command, so..."""
        users_timers = await self.get_user_timers(user_id)
        await self._do_timer_delete(users_timers)

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self, payload: discord.raw_models.RawReactionActionEvent
    ):
        """Watches for bell reactions on timer messages.

        Thank you SinbadCogs!
        https://github.com/mikeshardmind/SinbadCogs/blob/v3/rolemanagement/events.py
        """
        if not payload.guild_id or await self.bot.cog_disabled_in_guild_raw(
            self.qualified_name, payload.guild_id
        ):
            return
        if str(payload.emoji) != self.timer_emoji:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if member.bot:
            return

        try:
            timer = self.me_too_timers[payload.message_id]
            users_timers = await self.get_user_timers(member.id)
            timer["USER_ID"] = member.id
            if self._timer_exists(users_timers, timer):
                return
            timer["USER_TIMER_ID"] = self.get_next_user_timer_id(
                users_timers
            )
            async with self.config.timers() as current_timers:
                current_timers.append(timer)
            message = "Hello! I will also send you that timer"
            if timer["REPEAT"]:
                human_repeat = htd(seconds=timer["REPEAT"])
                message += f" every {human_repeat}"
                if human_repeat != timer["FUTURE_TEXT"]:
                    message += (
                        f", with the first timer in {timer['FUTURE_TEXT']}."
                    )
                else:
                    message += "."
            else:
                message += f" in {timer['FUTURE_TEXT']}."

            await member.send(message)
        except KeyError:
            return

    async def get_user_timers(self, user_id: int):
        """Return all of a users timers."""
        result = []
        async with self.config.timers() as current_timers:
            for timer in current_timers:
                if timer["USER_ID"] == user_id:
                    result.append(timer)
        return result

    @staticmethod
    def get_next_user_timer_id(timer_list):
        """Get the next timer ID for a user."""
        next_timer_id = 1
        used_timer_ids = set()
        for timer in timer_list:
            used_timer_ids.add(timer["USER_TIMER_ID"])
        while next_timer_id in used_timer_ids:
            next_timer_id += 1
        return next_timer_id

    @staticmethod
    def _timer_exists(timer_list, timer):
        """Check if a timer is already in this timer list (ignores user timer ID)."""
        for existing_timer in timer_list:
            if (
                existing_timer["USER_ID"] == timer["USER_ID"]
                and existing_timer["TIMER"] == timer["TIMER"]
                and existing_timer["FUTURE"] == timer["FUTURE"]
                and existing_timer["FUTURE_TEXT"] == timer["FUTURE_TEXT"]
            ):
                return True
        return False

    async def bg_loop(self):
        """Background loop."""
        await self.bot.wait_until_ready()
        while True:
            await self.check_timers()
            await asyncio.sleep(5)

    async def check_timers(self):
        """Send timers that have expired."""
        to_remove = []
        for timer in await self.config.timers():
            current_time_seconds = int(current_time.time())
            if timer["FUTURE"] <= current_time_seconds:
                user = self.bot.get_user(timer["USER_ID"])
                channel = self.bot.get_channel(timer["JUMP_LINK"])
                if user is None:
                    # Can't see the user (no shared servers): delete timer
                    to_remove.append(timer)
                    continue

                delay = current_time_seconds - timer["FUTURE"]
                reason = f"(for: **{timer['TIMER']}**)" if timer["TIMER"] != "" else ""
                if len(reason) > 200:
                    reason = reason[:196] + " ..."
                message = f"⏰ Hey {user.mention}, your {timer['FUTURE_TEXT']} of timer is up! {reason}"
                if delay > self.SEND_DELAY_SECONDS:
                    message += (
                        "\n\n⚠️ Due to issues with Discord, this timer was delayed"
                        + f" by {htd(seconds=delay)}. Sorry about that!\n"
                    )
                if "REPEAT" in timer and timer["REPEAT"]:
                    message += (
                        "\nℹ This is a repeating timer every "
                        f"{htd(seconds=max(timer['REPEAT'], 60))}."
                    )

                try:
                    await channel.send(message)
                except (discord.Forbidden, discord.NotFound):
                    # Can't send DM's to user: delete timer
                    to_remove.append(timer)
                except discord.HTTPException:
                    # Something weird happened: retry next time
                    pass
                else:
                    total_sent = await self.config.total_sent()
                    await self.config.total_sent.set(total_sent + 1)
                    to_remove.append(timer)
        if to_remove:
            async with self.config.timers() as current_timers:
                for timer in to_remove:
                    try:
                        new_timer = None
                        if "REPEAT" in timer and timer["REPEAT"]:
                            new_timer = timer.copy()
                            if new_timer["REPEAT"] < 60:
                                new_timer["REPEAT"] = 60
                            while new_timer["FUTURE"] <= int(current_time.time()):
                                new_timer["FUTURE"] += new_timer["REPEAT"]
                            new_timer["FUTURE_TEXT"] = htd(seconds=new_timer["REPEAT"])
                        current_timers.remove(timer)
                        if new_timer:
                            current_timers.append(new_timer)
                    except ValueError:
                        pass
