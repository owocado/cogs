import aiohttp
import asyncio
import datetime
import re

from bs4 import BeautifulSoup
from collections import OrderedDict
from dateutil import relativedelta
from io import BytesIO
from typing import Pattern

import discord
from redbot.core import commands
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import bold, box, humanize_number, inline, pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

INVITE_URL_REGEX: Pattern = re.compile(
    r"((https:\/\/)?(discord|discordapp)\.(com|gg)\/(invite)?\/?[\w-]+)"
)


class Utilities(commands.Cog):
    """Some of my useful & fun utility commands, grouped in one cog."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.0.6"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command()
    async def snowflake(self, ctx: commands.Context, snowflake: int, snowflake2: int = None):
        """Convert a snowflake to human relative datetime timedelta

        or compare timedelta difference between 2 snowflakes.
        """
        to_match = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        try:
            snowflake = discord.utils.snowflake_time(snowflake)
        except (ValueError, OverflowError):
            await ctx.send("Value of given `snowflake` parameter is out of range.")
            return
        if snowflake2 is None:
            snowflake2 = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        else:
            try:
                snowflake2 = discord.utils.snowflake_time(snowflake2)
            except (ValueError, OverflowError):
                await ctx.send("Value of given `snowflake2` parameter is out of range.")
                return

        diff = self._accurate_timedelta(snowflake, snowflake2, 5)
        strftime1 = snowflake.strftime("%d %b, %Y at %H:%M:%S")
        strftime2 = "**Time 2:** " + snowflake2.strftime("%d %b, %Y at %H:%M:%S") + " UTC\n" if snowflake2 == to_match else ""
        when = "ago" if snowflake2 > snowflake else "in future"

        final_message = (
            f"**Time  :** {strftime1} UTC\n{strftime2}"
            f"**Diff  :** {diff} {when}"
        )

        await ctx.send(final_message)

    @commands.command()
    async def inviscount(self, ctx: commands.Context, *, role: discord.role):
        """Get number (and %) of offline users in a given role."""
        if role is None:
            return await ctx.send("Please provide a valid role name or role ID.")

        users = [a for a in ctx.guild.members if role in a.roles]
        count = len([m for m in ctx.guild.members if role in m.roles])
        if count == 0:
            return await ctx.send(f"No one has `{role.name}` role yet. 🤔")
        offline = sum(x.status == discord.Status.offline for x in users)
        percent = offline / count

        to_send = (
            f"({round(percent * 100, 2)}%) __**{offline}**__ out of "
            f"{count} users in **{role.name}** role are currently offline."
        )
        await ctx.send(to_send)

    @commands.command(aliases=["urlshorten"])
    async def bitly(self, ctx: commands.Context, url: str, custom_bitlink: str = None):
        """Generate a shortened URL with Bitly API.

        `custom_bitlink` needs to be in format: `bit.ly/yourvanitycode`

        This command requires a generic access token from Bitly.
        You can get one for free from: https://bitly.is/accesstoken
        You will be require to register for an account first.

        Once you have the token, set it with:
        ```
        [p]set api bitly api_key <access_token>
        ```
        """
        api_key = (await ctx.bot.get_shared_api_tokens("bitly")).get("api_key")
        if api_key is None:
            return await ctx.send_help()

        head = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
        payload = {"long_url": url, "domain": "bit.ly"}
        base_url = "https://api-ssl.bitly.com/v4/shorten"
        await ctx.trigger_typing()
        try:
            async with self.session.post(base_url, headers=head, json=payload) as response:
                if not (300 > response.status >= 200):
                    return await ctx.send(f"https://http.cat/{response.status}")
                data = await response.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        link = data.get("link", "Missing shortened URL.")

        if custom_bitlink is None:
            return await ctx.send(link)

        bitlink_id = data.get("id", "bitly.is ID missing.").replace("bitly.is", "bit.ly")
        xpayload = {"custom_bitlink": custom_bitlink, "bitlink_id": bitlink_id}
        xbase_url = "https://api-ssl.bitly.com/v4/custom_bitlinks"
        try:
            async with self.session.post(xbase_url, headers=head, json=xpayload) as resp:
                if not (300 > resp.status >= 200):
                    return await ctx.send(f"https://http.cat/{resp.status}")
                output = await resp.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        custom_link = output.get("bitlink").get("custom_bitlinks")[0]
        await ctx.send(custom_link)

    @commands.command()
    @commands.is_owner()
    @commands.bot_has_permissions(attach_files=True)
    async def thumio(self, ctx: commands.Context, url: str):
        """Get a free landspace screenshot of a valid publicly accessible webpage."""
        base_url = f"https://image.thum.io/get/width/1920/crop/675/noanimate/{url}"
        await ctx.trigger_typing()
        try:
            async with self.session.get(base_url) as resp:
                if resp.status != 200:
                    return await ctx.send(f"https://http.cat/{resp.status}")
                data = BytesIO(await resp.read())
                data.seek(0)
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        await ctx.send(file=discord.File(data, "screenshot.png"))

    @commands.command()
    @commands.is_owner()
    @commands.bot_has_permissions(attach_files=True)
    async def screenshot(
        self,
        ctx: commands.Context,
        web_url: str,
        full_page: str = "false",
        width: int = 1680,
        height: int = 876,
        fresh: str = "true",
        block_ads: str = "false",
        no_cookie_banners: str = "false",
        omit_background: str = "false",
        dark_mode: str = "false",
        lazy_load: str = "false",
        destroy_screenshot: str = "true",
    ):
        """Get a screenshot of a valid publicly accessible webpage.

        This command requires an API token. You can get a free token
        by registering a free account on https://screenshotapi.net

        Once you have the API token, set it with:
        ```
        [p]set api screenshotapi api_key <api_token>
        ```
        Please note: free API token quota is limited to 100 screenshots per month.
        """
        api_key = (await ctx.bot.get_shared_api_tokens("screenshotapi")).get("api_key")
        if api_key is None:
            return await ctx.send_help()

        full_page = "false" if full_page not in ["true", "false"] else full_page
        width = 1920 if 100 > width > 7680 else width
        height = 1080 if 100 > height > 4320 else height
        fresh = "true" if fresh not in ["true", "false"] else fresh
        block_ads = "false" if block_ads not in ["true", "false"] else block_ads
        no_cookie_banners = "false" if no_cookie_banners not in ["true", "false"] else no_cookie_banners
        omit_background = "false" if omit_background not in ["true", "false"] else omit_background
        dark_mode = "false" if dark_mode not in ["true", "false"] else dark_mode
        lazy_load = "false" if lazy_load not in ["true", "false"] else lazy_load
        destroy_screenshot = "true" if destroy_screenshot not in ["true", "false"] else destroy_screenshot

        base_url = "https://shot.screenshotapi.net/screenshot"
        params = {
            "token": api_key,
            "url": web_url,
            "width": width,
            "height": height,
            "full_page": full_page,
            "fresh": fresh,
            "output": "image",
            "file_type": "png",
            "block_ads": block_ads,
            "no_cookie_banners": no_cookie_banners,
            "destroy_screenshot": destroy_screenshot,
            "dark_mode": dark_mode
        }

        await ctx.trigger_typing()
        try:
            async with self.session.get(base_url, params=params) as response:
                if response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                data = BytesIO(await response.read())
                data.seek(0)
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        await ctx.send(file=discord.File(data, "screenshot.png"))

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def seenlist(self, ctx: commands.Context):
        """Fetch a list of last seen time of all the server members."""
        # I mainly made this for my own convenience and personal use some time ago,
        # making it public in case someone finds it useful.

        cog = self.bot.get_cog("Seen")
        if not cog:
            return await ctx.send("This command requires Seen cog to be loaded.")

        seen_list = ""
        data = await cog.config.all_members(ctx.guild)
        sorted_data = OrderedDict(sorted(data.items(), key=lambda i: i[1]['seen']))
        async for user, seen in AsyncIter(sorted_data.items()):
            if ctx.guild.get_member(user):
                now_dt = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                seen_dt = datetime.datetime.utcfromtimestamp(seen.get("seen"))
                seen_delta = self._accurate_timedelta(now_dt, seen_dt, 3)
                seen_list += f"seen {seen_delta:>20} ago | {ctx.guild.get_member(user)}\n"
            else:
                seen_list += ""
        embed_list = []
        pages = []
        for page in pagify(seen_list, ["\n"], page_length=750):
            pages.append(box(page))
        max_i = len(pages)
        i = 1
        for page in pages:
            embed_list.append(f"Page `{i}` of `{max_i}`:\n\n" + page)
            i += 1
        if not embed_list:
            return await ctx.send("No results.")
        elif len(embed_list) == 1:
            return await ctx.send(embed_list[0])
        else:
            await menu(ctx, embed_list, DEFAULT_CONTROLS, timeout=60.0)

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def inviteinfo(self, ctx: commands.Context, invite_link_or_code: str):
        """Get some basic info about a Discord invite and it's parent guild."""
        match = INVITE_URL_REGEX.match(invite_link_or_code)
        invite_link_or_code = match.group(1).split("/")[-1] if match else invite_link_or_code

        try:
            invite = await self.bot.fetch_invite(invite_link_or_code)
        except (discord.NotFound, discord.HTTPException):
            return await ctx.send("The invite is either invalid or has expired.")

        verif_lvl = "**Server verification level:**  " + str(invite.guild.verification_level).title()
        created_on = invite.guild.created_at
        now = ctx.message.created_at
        created_delta = self._accurate_timedelta(now, created_on, 2) + " ago"
        guild_info = (
            f"Server ID: {invite.guild.id} • "
            f"Server created ({created_delta}) on"
        )
        embed = discord.Embed(
            description=(f"{invite.guild.description}\n\n" if invite.guild.description else "\n") + verif_lvl,
            colour=await ctx.embed_colour(),
        )
        # attribution : https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/cogs/general/general.py#L412
        embed.set_author(
            name="Invite Info for: " + str(invite.guild.name),
            icon_url="https://cdn.discordapp.com/emojis/457879292152381443.png"
            if "VERIFIED" in invite.guild.features
            else "https://cdn.discordapp.com/emojis/508929941610430464.png"
            if "PARTNERED" in invite.guild.features
            else discord.Embed.Empty,
        )
        embed.timestamp = created_on
        embed.set_footer(text=guild_info)
        embed.set_thumbnail(url=str(invite.guild.icon_url))
        online_emoji = discord.utils.get(self.bot.emojis, id=749221433552404581)
        online_emoji = online_emoji if online_emoji else "\N{LARGE GREEN CIRCLE}"
        offline_emoji = discord.utils.get(self.bot.emojis, id=749221433049088082)
        offline_emoji = offline_emoji if offline_emoji else "\N{MEDIUM WHITE CIRCLE}"
        approx_total = humanize_number(invite.approximate_member_count)
        approx_online = humanize_number(invite.approximate_presence_count)
        users_count = f"{online_emoji} {approx_online} Online\n{offline_emoji} {approx_total} Total"
        embed.add_field(name="Approx. Users", value=users_count)
        if invite.inviter:
            embed.add_field(name="Inviter", value=str(invite.inviter))
        else:
            embed.add_field(name="Vanity invite?", value="✅ Most likely")
        embed.add_field(
            name="Invite channel",
            value=f"#{invite.channel.name}\n{inline(f'<#{invite.channel.id}>')}",
        )
        # embed.add_field(name="Server ID", value=str(invite.guild.id))
        # embed.add_field(name="Verification Level", value=verif_lvl)
        assets_info = f"[Server Icon]({invite.guild.icon_url})"
        if invite.guild.banner:
            assets_info += f" • [Server Banner]({invite.guild.banner_url_as(format='png', size=2048)})"
        if invite.guild.splash:
            assets_info += f" • [Invite Splash]({invite.guild.splash_url_as(format='png', size=2048)})"
        embed.add_field(name="Server Assets", value=assets_info)
        if invite.guild.features:
            embed.add_field(
                name="Server features",
                value="\n".join("• " + x.replace("_", " ").title() for x in sorted(invite.guild.features)),
                inline=False,
            )
        if invite.guild.id in [x.id for x in self.bot.guilds]:
            embed.add_field(
                name="\u200b",
                value="Oh look, I am a member of this server. 😃",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command(aliases=["kymeme"])
    @commands.bot_has_permissions(embed_links=True)
    async def knowyourmeme(self, ctx: commands.Context, *, query: str):
        """Searches Know Your Meme for your meme query."""
        base_url = f"https://knowyourmeme.com/search?q={query}"
        user_agent = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
        }

        await ctx.trigger_typing()
        try:
            async with self.session.get(base_url, headers=user_agent) as response:
                if response.status != 200:
                    await ctx.send(f"https://http.cat/{response.status}")
                    return
                data = BeautifulSoup(await response.content.read(), "html.parser")
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out.")
            return

        meme_endpoint = data.findAll("tbody")[0].tr.td.a["href"]
        meme_url = "https://knowyourmeme.com" + str(meme_endpoint)

        await ctx.send(meme_url)

    @commands.command(name="unredirect")
    async def unredirect_url(self, ctx: commands.Context, url: str):
        """Find out where those pesky shady redirect URLs leads you to."""
        url = url.lstrip("<").rstrip(">")

        await ctx.trigger_typing()
        try:
            async with self.session.get(url, allow_redirects=False) as response:
                if not response.status in [300, 301, 302, 303, 304, 305, 306, 307, 308]:
                    await ctx.send("Provided URL is not a redirect URL. 🤔")
                    return
                # Code attribution and credits to original author : https://stackoverflow.com/a/49091337
                url_meta = str(response).split("Location': \'")[1].split("\'")[0]
        except aiohttp.InvalidURL:
            return await ctx.send("You provided an invalid URL. Trying to make me error huh? 😏")
        except (asyncio.TimeoutError, IndexError):
            return await ctx.send("Operation timed out.")

        to_send = f"**Given URL redirects to:**\n\n{url_meta}"
        await ctx.maybe_send_embed(to_send)

    @staticmethod
    def _accurate_timedelta(value1, value2, index: int):
        if value1 > value2:
            diff = relativedelta.relativedelta(value1, value2)
        else:
            diff = relativedelta.relativedelta(value2, value1)

        yrs, mths, days = (diff.years, diff.months, diff.days)
        hrs, mins, secs = (diff.hours, diff.minutes, diff.seconds)

        pretty = f"{yrs}y {mths}mth {days}d {hrs}h {mins}m {secs}s"
        to_join = " ".join([x for x in pretty.split() if x[0] != '0'][:index])

        return to_join
