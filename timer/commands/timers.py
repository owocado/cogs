import asyncio
import re
import time as current_time
from abc import ABC
from datetime import timedelta

import discord
from redbot.core import commands
from redbot.core.commands import BadArgument, Context, parse_timedelta
from redbot.core.utils.chat_formatting import humanize_timedelta as htd
from redbot.core.utils.predicates import MessagePredicate

from ..abc import CompositeMetaClass, MixinMeta
from ..pcx_lib import delete, embed_splitter, reply


class TimerCommands(MixinMeta, ABC, metaclass=CompositeMetaClass):
    def __init__(self):
        optional_in_every = r"(in\s+|every\s+)?"
        amount_and_time = r"\d+\s*(weeks?|w|days?|d|hours?|hrs|hr?|minutes?|mins?|m(?!o)|seconds?|secs?|s)"
        optional_comma_space_and = r"[\s,]*(and)?\s*"

        self.timedelta_begin = re.compile(
            r"^"
            + optional_in_every
            + r"("
            + amount_and_time
            + r"("
            + optional_comma_space_and
            + amount_and_time
            + r")*"
            + r")"
            + r"\b"
        )
        self.timedelta_end = re.compile(
            r"\b"
            + optional_in_every
            + r"("
            + amount_and_time
            + r"("
            + optional_comma_space_and
            + amount_and_time
            + r")*"
            + r")"
            + r"$"
        )

    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def timer(self, ctx: Context, *, time_and_optional_text: str = ""):
        """Create a timer with optional timer text.

        `<time>` supports commas, spaces, and "and":
        • i.e. `12h30m`, `6 hours and 15 minutes`

        Accepts seconds, minutes, hours, upto 1 day.

        Add `every <repeat_time>` to the command for repeating timers.

        Examples:
        `[p]timer in 8min45sec to do that thing`
        `[p]timer to water my plants in 2 hours`
        `[p]timer every 8h`
        """
        await self._create_timer(ctx, time_and_optional_text)

    @timer.command()
    async def list(self, ctx: Context, sort: str = "time"):
        """Show a list of all of your timers.

        Sort can either be:
        `time` (default) for soonest expiring timer first,
        `added` for ordering by when the timer was added,
        `id` for ordering by ID
        """
        to_send = await self.get_user_timers(ctx.author.id)
        if sort == "time":
            to_send.sort(key=lambda timer_info: timer_info["FUTURE"])
        elif sort == "added":
            pass
        elif sort == "id":
            to_send.sort(key=lambda timer_info: timer_info["USER_TIMER_ID"])
        else:
            return await reply(
                ctx,
                "Valid sorting options are: `time` (default), `added`, or `id`.",
            )

        if not to_send:
            return await reply(ctx, "You don't have any upcoming timers.")

        embed = discord.Embed(color=await ctx.embed_color())
        embed.set_author(
            name=f"{ctx.author.name}'s pending timers:",
            icon_url=str(ctx.author.display_avatar.url),
        )
        current_time_seconds = int(current_time.time())
        timer_text = ""
        for timer in to_send:
            delta = timer["FUTURE"] - current_time_seconds
            timer_text += (
                f"**[`{timer['USER_TIMER_ID']}`]**  <t:{timer['FUTURE']}:R>"
                f"{' (for: ' + timer['TIMER'] + ')' if timer['TIMER'] != ''  else ''}\n"
            )
            if "REPEAT" in timer and timer["REPEAT"]:
                timer_text += f"ℹ  *repeating every `{htd(seconds=timer['REPEAT'])}`*\n"

        embed.description = timer_text
        await embed_splitter(embed, ctx.channel)

    @timer.group(aliases=["edit"])
    async def modify(self, ctx: Context):
        """Modify an existing timer."""
        pass

    @modify.command()
    async def time(self, ctx: Context, timer_id: int, *, time: str):
        """Modify the time of an existing timer."""
        users_timers = await self.get_user_timers(ctx.author.id)
        old_timer = self._get_timer(users_timers, timer_id)
        if not old_timer:
            return await self._send_non_existent_msg(ctx, timer_id)

        try:
            time_delta = parse_timedelta(
                time, maximum=timedelta(hours=24), minimum=timedelta(seconds=20)
            )
            if not time_delta:
                return await ctx.send(
                    "❌ I couldn't understand the format of your timer time or text."
                )
        except BadArgument as ba:
            return await reply(ctx, str(ba))
        future = int(current_time.time() + time_delta.total_seconds())
        future_text = htd(timedelta=time_delta)

        new_timer = old_timer.copy()
        new_timer.update(FUTURE=future, FUTURE_TEXT=future_text)
        async with self.config.timers() as current_timers:
            current_timers.remove(old_timer)
            current_timers.append(new_timer)
        message = (
            f"Timer with ID# **{timer_id}** will now ping you <t:{future}:R>"
        )
        if "REPEAT" in new_timer and new_timer["REPEAT"]:
            message += f", repeating every {htd(seconds=new_timer['REPEAT'])} thereafter."
        else:
            message += "."
        await reply(ctx, message)

    @modify.command()
    async def repeat(self, ctx: Context, timer_id: int, *, time: str):
        """Modify the repeating time of an existing timer.

        Pass "0" to <time> in order to disable repeating.
        """
        users_timers = await self.get_user_timers(ctx.author.id)
        old_timer = self._get_timer(users_timers, timer_id)
        if not old_timer:
            return await self._send_non_existent_msg(ctx, timer_id)

        if time.lower() in ["0", "stop", "none", "false", "no", "cancel", "n"]:
            new_timer = old_timer.copy()
            new_timer.update(REPEAT=None)
            async with self.config.timers() as current_timers:
                current_timers.remove(old_timer)
                current_timers.append(new_timer)
            await reply(
                ctx,
                f"Timer with ID# **{timer_id}** will not repeat anymore. "
                f"The final timer will be sent <t:{new_timer['FUTURE']}:R>.",
            )
        else:
            try:
                time_delta = parse_timedelta(
                    time,
                    maximum=timedelta(hours=24),
                    minimum=timedelta(minutes=1),
                    allowed_units=["hours", "minutes"]
                )
                if not time_delta:
                    return await ctx.send(
                        "❌ I couldn't understand the format of your timer time or text."
                    )
            except BadArgument as ba:
                return await reply(ctx, str(ba))

            new_timer = old_timer.copy()
            new_timer.update(REPEAT=int(time_delta.total_seconds()))
            async with self.config.timers() as current_timers:
                current_timers.remove(old_timer)
                current_timers.append(new_timer)
            await reply(
                ctx,
                f"Timer with ID# **{timer_id}** will now ping you every "
                f"{htd(timedelta=time_delta)}, with the first timer <t:{new_timer['FUTURE']}:R>.",
            )

    @modify.command()
    async def text(self, ctx: Context, timer_id: int, *, text: str):
        """Modify the text of an existing timer."""
        users_timers = await self.get_user_timers(ctx.author.id)
        old_timer = self._get_timer(users_timers, timer_id)
        if not old_timer:
            return await self._send_non_existent_msg(ctx, timer_id)

        text = text.strip()
        if len(text) > 200:
            return await reply(ctx, "Your timer text is too long.")


        new_timer = old_timer.copy()
        new_timer.update(TIMER=text)
        async with self.config.timers() as current_timers:
            current_timers.remove(old_timer)
            current_timers.append(new_timer)
        await reply(
            ctx,
            f"Timer with ID# **{timer_id}** has been edited successfully.",
        )

    @timer.command(aliases=["delete", "del"])
    async def remove(self, ctx: Context, index: str):
        """Delete a timer.

        <index> can either be:
        - a number for a specific timer to delete
        - `last` to delete the most recently created timer
        - `all` to delete all timers (same as [p]forgetme)
        """
        await self._delete_timer(ctx, index)

    @commands.command()
    async def ftimers(self, ctx: Context):
        """Remove all of your upcoming timers."""
        await self._delete_timer(ctx, "all")

    async def _create_timer(
        self, ctx: Context, time_and_optional_text: str
    ):
        """Logic to create a timer."""
        maximum = await self.config.max_user_timers()
        users_timers = await self.get_user_timers(ctx.author.id)
        if len(users_timers) > maximum - 1:
            plural = "timer" if maximum == 1 else "timers"
            return await reply(
                ctx,
                "You have too many timers! " +
                f"I can only keep track of {maximum} {plural} for you at a time.",
            )

        if ctx.message.reference:
            message = ctx.message.reference.resolved
            em = message.embeds
            RGX = re.compile(r"00`\*+h\*+ |\*+|`+|!+")
            if em and em[0].fields and message.author.id == 172002275412279296:
                time_and_optional_text = re.sub(RGX, "", em[0].fields[0].value)
            elif em and em[0].title and em[0].description and message.author.id == 824029844496056364:
                time_and_optional_text = re.sub(RGX, "", em[0].title + " " + em[0].description)
            else:
                time_and_optional_text = message.content.rstrip("*_.`!")

        try:
            (
                timer_time,
                timer_time_repeat,
                timer_text,
            ) = self._process_timer_text(time_and_optional_text.strip())
        except BadArgument as ba:
            return await reply(ctx, str(ba))
        if not timer_time:
            return await ctx.send(
                "❌ I couldn't understand the format of your timer time or text."
            )
        if len(timer_text) > 200:
            return await reply(ctx, "Your timer text is too long.")

        match = "You can [vote again on top.gg](https://top.gg/bot/172002275412279296/vote)"
        if timer_text == match:
            timer_text = "tatsu vote"

        next_timer_id = self.get_next_user_timer_id(users_timers)
        repeat = (
            int(timer_time_repeat.total_seconds()) if timer_time_repeat else None
        )
        future = int(current_time.time() + timer_time.total_seconds())
        future_text = htd(timedelta=timer_time)

        timer = {
            "USER_TIMER_ID": next_timer_id,
            "USER_ID": ctx.author.id,
            "TIMER": timer_text,
            "REPEAT": repeat,
            "FUTURE": future,
            "FUTURE_TEXT": future_text,
            "JUMP_LINK": ctx.channel.id,
        }
        async with self.config.timers() as current_timers:
            current_timers.append(timer)
        message = f"Timer is set, **{ctx.author.name}**! I will ping you "
        if repeat:
            message += f"every {htd(timedelta=timer_time_repeat)}"
            if timer_time_repeat != timer_time:
                message += f", with the first timer <t:{future}:R>."
        else:
            message += f"<t:{future}:R>."
        await reply(ctx, message)

        if (
            ctx.guild
            and await self.config.guild(ctx.guild).me_too()
            and ctx.channel.permissions_for(ctx.me).add_reactions
        ):
            query: discord.Message = await ctx.send(
                f"If anyone else want this timer as well, click the alarm reaction below!"
            )
            self.me_too_timers[query.id] = timer
            await query.add_reaction(self.timer_emoji)
            await asyncio.sleep(30)
            await delete(query)
            del self.me_too_timers[query.id]

    def _process_timer_text(self, timer_text):
        """Process given timer text into timedeltas, removing them from the timer text.

        Takes all "every {time_repeat}", "in {time}", and "{time}" from the start of timer_text.
        At most one instance of "every {time_repeat}", "in {time}" or "{time}" will be consumed.
        If the parser runs into a timedelta (in or every) that has already been parsed,
        parsing stops. Same process is then repeated from the end of the string.

        If an "every" time is provided but no "in" time,
        the "every" time will be copied over to the "in" time.
        """

        timer_time = None
        timer_time_repeat = None
        # find the time delta(s) at the beginning of the text
        (
            timer_time,
            timer_time_repeat,
            timer_text,
        ) = self._process_timer_text_from_ends(
            timer_time, timer_time_repeat, timer_text, self.timedelta_begin
        )
        # find the time delta(s) at the end of the text
        (
            timer_time,
            timer_time_repeat,
            timer_text,
        ) = self._process_timer_text_from_ends(
            timer_time, timer_time_repeat, timer_text, self.timedelta_end
        )
        # cleanup
        timer_time = timer_time or timer_time_repeat
        if len(timer_text) > 1 and timer_text[0:2] == "to":
            timer_text = timer_text[2:].strip()
        return timer_time, timer_time_repeat, timer_text

    def _process_timer_text_from_ends(
        self, timer_time, timer_time_repeat, timer_text, search_regex
    ):
        """Repeatedly regex search and modify the timer_text looking for all instances of timedeltas."""
        while regex_result := search_regex.search(timer_text):
            repeating = regex_result[1] and regex_result[1].strip() == "every"
            if (repeating and timer_time_repeat) or (
                not repeating and timer_time
            ):
                break
            parsed_timedelta = self._parse_timedelta(regex_result[2], repeating)
            if not parsed_timedelta:
                break
            timer_text = (
                timer_text[0: regex_result.span()[0]]
                + timer_text[regex_result.span()[1] + 1:]
            ).strip()
            if repeating:
                timer_time_repeat = parsed_timedelta
            else:
                timer_time = parsed_timedelta
        return timer_time, timer_time_repeat, timer_text

    @staticmethod
    def _parse_timedelta(timedelta_string, repeating):
        """Parse a timedelta, taking into account if it is a repeating timedelta or not."""
        result = None
        testing_text = ""
        for chunk in timedelta_string.split():
            if chunk == "and":
                continue
            if chunk.isdigit():
                testing_text += chunk
                continue
            testing_text += chunk.rstrip(",")
            if repeating:
                try:
                    parsed = parse_timedelta(
                        testing_text,
                        maximum=timedelta(hours=24),
                        minimum=timedelta(minutes=1),
                        allowed_units=["hours", "minutes"],
                    )
                except BadArgument as ba:
                    orig_message = str(ba)[0].lower() + str(ba)[1:]
                    raise BadArgument(
                        f"For the repeating timers, {orig_message}. "
                    )
            else:
                parsed = parse_timedelta(
                    testing_text, maximum=timedelta(hours=24), minimum=timedelta(seconds=20)
                )
            if parsed != result:
                result = parsed
            else:
                return None
        return result

    async def _delete_timer(self, ctx: Context, index: str):
        """Logic to delete timers."""
        if not index:
            return
        users_timers = await self.get_user_timers(ctx.author.id)

        if not users_timers:
            return await reply(ctx, "You don't have any upcoming timers.")

        if index == "all":
            # Ask if the user really wants to do this
            pred = MessagePredicate.yes_or_no(ctx)
            await reply(
                ctx,
                "Are you **sure** you want to remove all of your timers? (yes/no)",
            )
            try:
                await ctx.bot.wait_for("message", check=pred, timeout=30)
            except asyncio.TimeoutError:
                return await reply(ctx, "I have left your timers alone.")
            if pred.result:
                await self._do_timer_delete(users_timers)
                return await reply(ctx, "All of your timers are now removed.")

        if index == "last":
            timer_to_delete = users_timers[len(users_timers) - 1]
            await self._do_timer_delete(timer_to_delete)
            return await reply(
                ctx,
                "Ok, I removed your last created timer! (ID# **{}**)".format(
                    timer_to_delete["USER_TIMER_ID"]
                ),
            )

        try:
            int_index = int(index)
        except ValueError:
            return await reply(ctx, "You provided invalid value for #ID.")

        timer_to_delete = self._get_timer(users_timers, int_index)
        if timer_to_delete:
            await self._do_timer_delete(timer_to_delete)
            await reply(ctx, f"Timer with ID# **{int_index}** has been removed.")
        else:
            await self._send_non_existent_msg(ctx, int_index)

    async def _do_timer_delete(self, timers):
        """Actually delete a timer."""
        if not timers:
            return
        if not isinstance(timers, list):
            timers = [timers]
        async with self.config.timers() as current_timers:
            for timer in timers:
                current_timers.remove(timer)

    @staticmethod
    async def _send_non_existent_msg(ctx: Context, timer_id: int):
        """Send a message telling the user the timer ID does not exist."""
        await reply(
            ctx,
            f"Timer with ID# **{timer_id}** does not exist! " +
            "Check the timer list and verify you typed the correct ID#.",
        )

    @staticmethod
    def _get_timer(timer_list, timer_id: int):
        """Get the timer from timer_list with the specified timer_id."""
        for timer in timer_list:
            if timer["USER_TIMER_ID"] == timer_id:
                return timer
        return None
