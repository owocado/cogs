from datetime import datetime, timezone
from typing import Union

import discord
from dateutil import relativedelta
from redbot.core import Config, commands
from redbot.core.errors import CogLoadError
from redbot.core.utils.common_filters import filter_invites
from redbot.core.utils.menus import menu, next_page


class RouteV9(discord.http.Route):
    BASE = "https://discord.com/api/v9"


class Userinfo(commands.Cog):
    """Replace original Red userinfo command with more details."""

    __version__ = "1.1.1"

    def format_help_for_context(self, ctx):
        """Thanks Sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 95932766180343808, force_registration=True)
        default_global = {
            "status_emojis": {
                "mobile": 749067110931759185,
                "dnd_mobile": 884019767244099604,
                "idle_mobile": 884019766908575765,
                "online": 749221433552404581,
                "away": 749221433095356417,
                "dnd": 749221432772395140,
                "offline": 749221433049088082,
                "streaming": 749221434039205909,
            },
            "badge_emojis": {
                "staff": 848556248832016384,
                "discord_certified_moderator": 848556248357273620,
                "early_supporter": 706198530837970998,
                "hypesquad_balance": 706198531538550886,
                "hypesquad_bravery": 706198532998299779,
                "hypesquad_brilliance": 706198535846101092,
                "hypesquad": 706198537049866261,
                "verified_bot_developer": 706198727953612901,
                "bug_hunter": 848556247632052225,
                "bug_hunter_level_2": 706199712402898985,
                "partner": 848556249192202247,
                "verified_bot": 848561838974697532,
                "verified_bot2": 848561839260434482,
                "server_booster": 710871139227795487,
                "discord_nitro": 710871154839126036,
                "bot_tag": 848557763172892722,
            },
        }
        self.config.register_global(**default_global)
        self.emojis = self.bot.loop.create_task(self.init())

    def cog_unload(self):
        if self.emojis:
            self.emojis.cancel()
        # Remove command logic are from: https://github.com/mikeshardmind/SinbadCogs/tree/v3/messagebox
        global _old_userinfo
        global _old_names
        if _old_userinfo:
            self.bot.remove_command("userinfo")
            self.bot.add_command(_old_userinfo)
        if _old_names:
            self.bot.remove_command("names")
            self.bot.add_command(_old_names)

    async def init(self):
        await self.bot.wait_until_ready()
        await self.gen_emojis()

    # Credits to flare
    async def gen_emojis(self):
        config = await self.config.all()
        self.status_emojis = {
            "mobile": discord.utils.get(self.bot.emojis, id=config["status_emojis"]["mobile"]),
            "dnd_mobile": discord.utils.get(
                self.bot.emojis, id=config["status_emojis"]["dnd_mobile"]
            ),
            "idle_mobile": discord.utils.get(
                self.bot.emojis, id=config["status_emojis"]["idle_mobile"]
            ),
            "online": discord.utils.get(self.bot.emojis, id=config["status_emojis"]["online"]),
            "away": discord.utils.get(self.bot.emojis, id=config["status_emojis"]["away"]),
            "dnd": discord.utils.get(self.bot.emojis, id=config["status_emojis"]["dnd"]),
            "offline": discord.utils.get(self.bot.emojis, id=config["status_emojis"]["offline"]),
            "streaming": discord.utils.get(
                self.bot.emojis, id=config["status_emojis"]["streaming"]
            ),
        }
        self.badge_emojis = {
            "booster": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["server_booster"]
            ),
            "bot": discord.utils.get(self.bot.emojis, id=config["badge_emojis"]["bot_tag"]),
            "bug_hunter": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["bug_hunter"]
            ),
            "bug_hunter_level_2": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["bug_hunter_level_2"]
            ),
            "discord_certified_moderator": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["discord_certified_moderator"]
            ),
            "early_supporter": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["early_supporter"]
            ),
            "hypesquad": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["hypesquad"]
            ),
            "hypesquad_balance": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["hypesquad_balance"]
            ),
            "hypesquad_bravery": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["hypesquad_bravery"]
            ),
            "hypesquad_brilliance": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["hypesquad_brilliance"]
            ),
            "nitro": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["discord_nitro"]
            ),
            "partner": discord.utils.get(self.bot.emojis, id=config["badge_emojis"]["partner"]),
            "staff": discord.utils.get(self.bot.emojis, id=config["badge_emojis"]["staff"]),
            "verified_bot": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["verified_bot"]
            ),
            "verified_bot2": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["verified_bot2"]
            ),
            "verified_bot_developer": discord.utils.get(
                self.bot.emojis, id=config["badge_emojis"]["verified_bot_developer"]
            ),
        }

    @commands.group()
    @commands.is_owner()
    async def uinfoset(self, ctx):
        """Manage userinfo settings."""

    @uinfoset.command()
    async def setemoji(self, ctx, status_or_badge: str, type: str, emoji_id: int):
        """Set status or badge emoji"""
        if status_or_badge not in ["status", "badge"]:
            return await ctx.send("You must choose either status or badge.")
        if status_or_badge == "status":
            async with self.config.status_emojis() as emojis:
                if type not in emojis:
                    await ctx.send(
                        "That emoji doesn't exist. Valid emoji types are: {}".format(
                            ", ".join(emojis.keys())
                        )
                    )
                    return
                emojis[type] = emoji_id
        else:
            async with self.config.badge_emojis() as emojis:
                if type not in emojis:
                    await ctx.send(
                        "That emoji type doesn't exist. Valid emoji types are: {}".format(
                            ", ".join(emojis.keys())
                        )
                    )
                    return
                emojis[type] = emoji_id
        await self.gen_emojis()
        await ctx.tick()

    @uinfoset.command()
    async def clear(self, ctx):
        """Reset emojis to default."""
        await self.config.clear_all()
        await self.gen_emojis()
        await ctx.tick()

    # ATTRIBUTION: https://github.com/aikaterna/aikaterna-cogs/blob/v3/away/away.py#L37
    # Credits to aikaterna , TrustyJAID
    def _draw_play(self, song):
        song_start_time = song.start
        total_time = song.duration
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        elapsed_time = current_time - song_start_time
        sections = 12
        loc_time = round((elapsed_time / total_time) * sections)  # 10 sections

        bar_char = "\N{BOX DRAWINGS HEAVY HORIZONTAL}"
        seek_char = "\N{RADIO BUTTON}"
        play_char = "\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f"
        msg = "\n" + play_char + " "

        for i in range(sections):
            msg += seek_char if i == loc_time else bar_char

        msg += " `{:.7}`/`{:.7}`".format(str(elapsed_time), str(total_time))
        return msg

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def banner(self, ctx: commands.Context, *, user: Union[discord.Member, int]):
        """Get a user's profile banner.

        Said user must share a mutual guild with the bot for this to work.
        """
        if isinstance(user, int):
            try:
                user = await self.bot.get_or_fetch_user(user)
            except discord.NotFound:
                return await ctx.send("404 Not Found. You sure you passed a valid user ID?")

        embed = await self._get_banner(user)
        if not embed:
            return await ctx.send("I could not fetch profile banner of that user.")

        await ctx.send(embed=embed)

    async def _get_banner(self, user):
        data = await self.bot.http.request(RouteV9("GET", f"/users/{user.id}"))
        if data.get("banner") is None:
            return None

        embed = discord.Embed()
        embed.set_author(name=str(user), icon_url=str(user.avatar_url))
        b_hash = data["banner"]
        extension = "gif" if b_hash.startswith("a_") else "png"
        url = f"https://cdn.discordapp.com/banners/{user.id}/{b_hash}.{extension}?size=2048"
        embed.color = user.color
        embed.description = f"➡️    **[Direct link to Banner]({url})**"
        embed.set_image(url=url)
        return embed

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def userinfo(self, ctx: commands.Context, *, user: discord.Member = None):
        """Show userinfo with some more details."""
        await ctx.trigger_typing()
        mod = self.bot.get_cog("Mod")
        user = user or ctx.author

        sharedguilds = len(user.mutual_guilds) if user is not ctx.me else 0
        shared_guilds = f"**Shared Servers:** {sharedguilds}\n" if sharedguilds > 1 else ""
        roles = user.roles[-1:0:-1]

        joined_at = user.joined_at
        since_created = self._humanize_time(user.created_at)
        if joined_at:
            since_joined = self._humanize_time(joined_at)
            user_joined = f"<t:{round(joined_at.timestamp())}:d>"
        else:
            since_joined, user_joined = ("?", "Unknown")
        user_created = f"<t:{round(user.created_at.timestamp())}:d>"
        voice_state = user.voice
        member_i = sorted(ctx.guild.members, key=lambda m: m.joined_at or datetime.utcnow()).index(user) + 1

        created_on = f"**Account created**: {since_created} ago ({user_created})\n"
        joined_on = f"**Joined this server**: {since_joined} ago ({user_joined})\n"
        boosting_since = (
            f"**Boosting here since:** {self._humanize_time(user.premium_since)}"
            + f" ago (<t:{round(user.premium_since.timestamp())}:d>)\n"
            if user.premium_since
            else ""
        )
        dateinfo_to_join = created_on + joined_on + boosting_since

        if user.is_on_mobile() and user.status.name == "dnd":
            statusemoji = self.status_emojis["dnd_mobile"] or "📱 **(DND)**"
        elif user.is_on_mobile() and user.status.name == "idle":
            statusemoji = self.status_emojis["idle_mobile"] or "📱 **(IDLE)**"
        elif user.is_on_mobile():
            statusemoji = self.status_emojis["mobile"] or "📱"
        elif any(a.type == discord.ActivityType.streaming for a in user.activities):
            statusemoji = self.status_emojis["streaming"] or "🟣"
        elif user.status.name == "online":
            statusemoji = self.status_emojis["online"] or "🟢"
        elif user.status.name == "offline":
            statusemoji = self.status_emojis["offline"] or "⚪"
        elif user.status.name == "dnd":
            statusemoji = self.status_emojis["dnd"] or "🔴"
        elif user.status.name == "idle":
            statusemoji = self.status_emojis["away"] or "🟠"
        else:
            statusemoji = "⚫"
        activity = f"**Status**: {statusemoji}\n\n"
        status_string = mod.get_status_string(user)
        if status_string:
            status_string = "\n__**Activities**__:\n" + status_string

        spot = next((c for c in user.activities if isinstance(c, discord.Spotify)), None)
        spotify = f"{self._draw_play(spot)}" if spot else ""

        pages = []
        data = discord.Embed(colour=user.colour)
        data.description = activity + shared_guilds + dateinfo_to_join + status_string + spotify

        if roles:
            role_str = " ".join([x.mention for x in roles])
            # 400 BAD REQUEST (error code: 50035): Invalid Form Body
            # In embed.fields.2.value: Must be 500 or fewer in length.
            if len(role_str) > 500:
                available_length = 500 - 22

                role_chunks = []
                remaining_roles = 0

                for r in roles:
                    chunk = f"{r.mention} "
                    chunk_size = len(chunk)

                    if chunk_size < available_length:
                        available_length -= chunk_size
                        role_chunks.append(chunk)
                    else:
                        remaining_roles += 1
                role_chunks.append(f"+**{remaining_roles}** more roles.")

                role_str = "".join(role_chunks)

            data.add_field(
                name=f"Roles: ({len(roles)})" if len(roles) > 1 else "Role:",
                value=role_str,
                inline=False,
            )

        if voice_state and voice_state.channel:
            data.add_field(
                name="Connected to VC:",
                value="{0.mention} ID: `{0.id}`".format(voice_state.channel),
                inline=False,
            )

        names, nicks = await mod.get_names_and_nicks(user)
        if names:
            val = filter_invites(", ".join(names))
            data.add_field(
                name=f"Previous Usernames ({len(names)})"
                if len(names) > 1 else "Previous Username",
                value=val,
                inline=False,
            )
        if nicks:
            val = filter_invites(", ".join(nicks))
            data.add_field(
                name=f"Previous Nicknames ({len(nicks)})"
                if len(nicks) > 1 else "Previous Nickname",
                value=val,
                inline=False,
            )

        name = "  ".join((str(user), f"({user.nick})")) if user.nick else str(user)
        name = filter_invites(name)

        avatar = user.avatar_url_as(static_format="png", size=2048)
        data.set_author(name=name, url=avatar)
        data.set_thumbnail(url=avatar)

        v_emoji = f"{self.badge_emojis['verified_bot']}{self.badge_emojis['verified_bot2']}"
        flags = [f.name for f in user.public_flags.all()]
        badges = []
        if flags:
            for badge in flags:
                if badge == "verified_bot":
                    emoji = v_emoji
                else:
                    emoji = self.badge_emojis[badge]
                badges.append(emoji)
        if user.is_avatar_animated():
            badges.append(self.badge_emojis["nitro"])
        if user.premium_since:
            badges.append(self.badge_emojis["booster"])
            if not user.is_avatar_animated():
                badges.append(self.badge_emojis["nitro"])
        if user.bot and "verified_bot" not in flags:
            badges.append(self.badge_emojis["bot"])
        if badges:
            data.title = "  ".join(str(x) for x in badges)

        # ATTRIBUTION : https://github.com/Flame442/FlameCogs/blob/master/onlinestats/onlinestats.py#L50
        # Credits to Flame442
        d = str(user.desktop_status)
        m = str(user.mobile_status)
        w = str(user.web_status)
        if any([isinstance(a, discord.Streaming) for a in user.activities]):
            d = d if d == "offline" else "streaming"
            m = m if m == "offline" else "streaming"
            w = w if w == "offline" else "streaming"
        status = {
            "online": self.status_emojis["online"],
            "idle": self.status_emojis["away"],
            "dnd": self.status_emojis["dnd"],
            "offline": self.status_emojis["offline"],
            "streaming": self.status_emojis["streaming"],
        }
        desktop = f"{status[d]} Desktop App\n" if d != "offline" else ""
        mobile = f"{status[m]} Mobile App\n" if m != "offline" else ""
        web = f"{status[w]} Web Browser" if w != "offline" else ""
        devices = desktop + mobile + web
        if devices:
            data.add_field(name="Device Presence:", value=devices, inline=False)

        nth = self._get_suffix(member_i)
        footer = f"{member_i}{nth} member | User ID: {user.id}\n"

        banner = await self._get_banner(user)
        if banner:
            footer += "Click on ➡️ to view the profile banner."
            pages.append(banner)

        data.set_footer(text=footer)
        pages.append(data)

        if len(pages) == 1:
            return await ctx.send(embed=pages[0])
        else:
            right_arrow = {"➡️": next_page}
            await menu(ctx, pages[::-1], right_arrow)

    def _get_suffix(self, num: int):
        suffixes = {1: "st", 2: "nd", 3: "rd"}
        if 10 <= num % 100 <= 20:
            value = "th"
        else:
            value = suffixes.get(num % 10, "th")
        return value

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def names(self, ctx: commands.Context, *, member: discord.Member = None):
        """Show previous names and nicknames of a member."""
        member = member or ctx.author
        # member = member.pop(0)
        mod = self.bot.get_cog("Mod")
        names, nicks = await mod.get_names_and_nicks(member)

        embed = discord.Embed(colour=member.colour)
        embed.set_author(name=str(member), icon_url=member.avatar_url_as(static_format="png"))
        if names:
            header_1 = "Previous Username(s)"
            past_names = [f"`[{str(i + 1).zfill(2)}]` {x}" for i, x in enumerate(names)]
            embed.add_field(name=header_1, value="\n".join(past_names))
        if nicks:
            header_2 = "Previous nickname(s)"
            past_nicks = [f"`[{str(n + 1).zfill(2)}]` {m}" for n, m in enumerate(nicks)]
            embed.add_field(name=header_2, value="\n".join(past_nicks))
        if len(embed.fields) == 0:
            embed.description = "No past names records found."
        else:
            embed.set_footer(text="Sorted from oldest to newest.")

        await ctx.send(embed=embed)

    @staticmethod
    def _humanize_time(date_time):
        diff = relativedelta.relativedelta(datetime.utcnow(), date_time)

        yrs, mths, days = (diff.years, diff.months, diff.days)
        hrs, mins, secs = (diff.hours, diff.minutes, diff.seconds)

        pretty = f"{yrs}y {mths}mth {days}d {hrs}h {mins}m {secs}s"
        to_join = ", ".join([x for x in pretty.split() if x[0] != "0"][:3])

        return to_join


async def setup(bot):
    uinfo = Userinfo(bot)
    if "Mod" not in bot.cogs:
        raise CogLoadError("This cog requires the Mod cog to be loaded.")
    global _old_userinfo
    global _old_names
    _old_userinfo = bot.get_command("userinfo")
    _old_names = bot.get_command("names")
    if _old_userinfo:
        bot.remove_command(_old_userinfo.name)
    if _old_names:
        bot.remove_command(_old_names.name)
    bot.add_cog(uinfo)
