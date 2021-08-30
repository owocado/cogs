import asyncio
import re
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from io import BytesIO
from typing import Pattern

import aiohttp
import discord
from bs4 import BeautifulSoup as bsp
from dateutil import relativedelta
from redbot.core import commands
from redbot.core.commands import Context, GuildConverter
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import box, humanize_number, inline, pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, close_menu, menu

INVITE_URL_REGEX: Pattern = re.compile(
    r"((https:\/\/)?(discord|discordapp)\.(com|gg)\/(invite)?\/?[\w-]+)"
)


class Utilities(commands.Cog):
    """Some of my useful utility commands, grouped in one cog."""

    __author__ = "ow0x"
    __version__ = "0.1.0"

    def format_help_for_context(self, ctx: Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command()
    async def snowflake(self, ctx: Context, snowflake: int, snowflake2: int = None):
        """Convert/compare Discord snowflake IDs to human readable time difference.

        or compare timedelta difference between 2 snowflakes.
        """
        dt_now = datetime.now(timezone.utc).replace(tzinfo=None)
        try:
            dt_1 = discord.utils.snowflake_time(snowflake)
        except (ValueError, OverflowError):
            return await ctx.send(f"`{snowflake}` value is invalid or out of range.")

        if snowflake2:
            try:
                dt_2 = discord.utils.snowflake_time(snowflake2)
            except (ValueError, OverflowError):
                return await ctx.send(f"`{snowflake2}` value is invalid or out of range.")
        else:
            dt_2 = dt_now


        diff = self._time_diff(dt_1, dt_2, 5)
        tstamp_1 = f"`Timestamp 1:` <t:{int(dt_1.timestamp())}:f>"
        tstamp_2 = f"`Timestamp 2:` <t:{int(dt_2.timestamp())}:f>\n" if snowflake2 else ""

        final_message = f"{tstamp_1}\n{tstamp_2}\n`Difference :` {diff}"

        await ctx.send(final_message)

    @commands.command(name="inviscount")
    async def invisible_users_in_role(self, ctx: Context, *, role: discord.Role):
        """Get number (and %) of invisible users in a given role."""
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
            + f"{count} users in **{role.name}** role are currently offline."
        )
        await ctx.send(to_send)

    @commands.command(aliases=["urlshorten"])
    async def bitly(self, ctx: Context, url: str, custom_bitlink: str = None):
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
    async def thumio(self, ctx: Context, url: str):
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
        ctx: Context,
        web_url: str,
        full_page: bool = False,
        retina: bool = False,
        width: int = 1680,
        height: int = 876,
        fresh: str = "true",
        block_ads: bool = False,
        no_cookie_banners: str = "false",
        dark_mode: bool = True,
        destroy_screenshot: bool = False,
    ):
        """Get a screenshot of a publicly accessible webpage.

        This command requires an API token. You can get a free token
        by registering a free account on <https://screenshotapi.net>

        Once you have the API token, set it with:
        ```
        [p]set api screenshotapi api_key <api_token>
        ```
        Please note: free API token quota is limited to 100 screenshots per month.
        """
        api_key = (await ctx.bot.get_shared_api_tokens("screenshotapi")).get("api_key")
        if api_key is None:
            return await ctx.send_help()

        web_url = web_url.lstrip("<").rstrip(">")
        width = 1920 if (width < 100 or width > 7680) else width
        height = 1080 if (width < 100 or height > 4320) else height
        fresh = "true" if fresh not in ["true", "false"] else fresh
        no_cookie_banners = (
            "false" if no_cookie_banners not in ["true", "false"] else no_cookie_banners
        )

        base_url = "https://shot.screenshotapi.net/screenshot"
        params = {
            "token": api_key,
            "url": web_url,
            "width": width,
            "height": height,
            "full_page": full_page,
            "retina": retina,
            "fresh": fresh,
            "output": "image",
            "file_type": "png",
            "block_ads": block_ads,
            "no_cookie_banners": no_cookie_banners,
            "destroy_screenshot": destroy_screenshot,
            "dark_mode": dark_mode,
        }

        async with ctx.typing():
            try:
                async with self.session.post(base_url, json=params) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    data = BytesIO(await response.read())
                    data.seek(0)
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

        await ctx.send(ctx.author.mention, file=discord.File(data, "screenshot.png"))

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def inviteinfo(self, ctx: Context, invite_link_or_code: str):
        """Get some basic info about a Discord invite and it's parent guild."""
        match = INVITE_URL_REGEX.match(invite_link_or_code)
        invite_link_or_code = match.group(1).split("/")[-1] if match else invite_link_or_code

        try:
            invite = await self.bot.fetch_invite(invite_link_or_code)
        except (discord.NotFound, discord.HTTPException):
            return await ctx.send("The invite is either invalid or has expired.")

        verif_lvl = (
            "**Server verification level:**  " + str(invite.guild.verification_level).title()
        )
        created_on = invite.guild.created_at
        now = ctx.message.created_at
        created_delta = self._time_diff(now, created_on, 2) + " ago"
        guild_info = f"Server ID: {invite.guild.id} • Server created ({created_delta}) on"
        embed = discord.Embed(
            description=(f"{invite.guild.description}\n\n" if invite.guild.description else "\n")
            + verif_lvl,
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
        online_emoji = online_emoji or "\N{LARGE GREEN CIRCLE}"
        offline_emoji = discord.utils.get(self.bot.emojis, id=749221433049088082)
        offline_emoji = offline_emoji or "\N{MEDIUM WHITE CIRCLE}"
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
            assets_info += (
                f" • [Server Banner]({invite.guild.banner_url_as(format='png', size=2048)})"
            )
        if invite.guild.splash:
            assets_info += (
                f" • [Invite Splash]({invite.guild.splash_url_as(format='png', size=2048)})"
            )
        embed.add_field(name="Server Assets", value=assets_info)
        if invite.guild.features:
            embed.add_field(
                name="Server features",
                value="\n".join(
                    "• " + x.replace("_", " ").title() for x in sorted(invite.guild.features)
                ),
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
    async def knowyourmeme(self, ctx: Context, *, query: str):
        """Searches Know Your Meme for your meme query."""
        base_url = f"https://knowyourmeme.com/search?q={query}"
        user_agent = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
        }

        await ctx.trigger_typing()
        try:
            async with self.session.get(base_url, headers=user_agent) as response:
                if response.status != 200:
                    await ctx.send(f"https://http.cat/{response.status}")
                    return
                data = bsp(await response.content.read(), "html.parser")
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out.")
            return

        meme_endpoint = data.find_all("tbody")[0].tr.td.a["href"]
        meme_url = "https://knowyourmeme.com" + str(meme_endpoint)

        await ctx.send(meme_url)

    @commands.command(name="unredirect")
    async def unredirect_url(self, ctx: Context, url: str):
        """Find out where those pesky shady redirect URLs leads you to.

        Doesn't quite work against temporary redirects. :(
        """
        url = url.lstrip("<").rstrip(">")

        await ctx.trigger_typing()
        try:
            async with self.session.get(url, allow_redirects=False) as response:
                if not response.status in [300, 301, 302, 303, 304, 305, 306, 307, 308]:
                    return await ctx.send("Provided URL is not a permanent redirect URL. 🤔")
                # Code attribution and credits to original author : https://stackoverflow.com/a/49091337
                url_meta = str(response).split("Location': '")[1].split("'")[0]
        except aiohttp.InvalidURL:
            return await ctx.send("You provided an invalid URL. Trying to make me error huh? 😏")
        except (asyncio.TimeoutError, IndexError):
            return await ctx.send("Operation timed out.")

        to_send = f"**Given URL redirects to:**\n\n{url_meta}"
        await ctx.maybe_send_embed(to_send)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3.0, commands.BucketType.member)
    async def phub(self, ctx: Context, *, query: str):
        """Search PornHub for your kinky query. Only works in NSFW channels."""
        if not ctx.channel.is_nsfw():
            return await ctx.send("This command is only allowed in NSFW channels.")

        base_url = f"https://www.pornhub.com/video/search?search={query}"
        async with self.session.get(base_url) as response:
            if response.status != 200:
                return await ctx.send(f"https://http.cat/{response.status}")
            data = await response.text()

        if '<div class="noResultsWrapper">' in data:
            return await ctx.send("Could not find any results.")

        parsed_data = bsp(data, "html.parser")
        results = parsed_data.find_all("li", class_="pcVideoListItem js-pop videoblock videoBox")
        pages = []
        for i, css_soup in enumerate(results):
            # css_soup = bsp(result, "html.parser")
            video_key = css_soup["data-video-vkey"]
            video_link = f"https://www.pornhub.com/view_video.php?viewkey={video_key}"
            duration = f"**Duration:** {css_soup.find('var', class_='duration').text}\n"
            views = f"**Total views:** {css_soup.find('span', class_='views').text}\n"
            ratings = f"**Ratings/Likes:** {css_soup.find('div', class_='value').text}\n"
            created = css_soup.find("var", class_="added").text
            thumbnail = css_soup.find("img", class_="rotating")["data-path"]
            video_title = css_soup.find("a", class_="")["title"]
            embed = discord.Embed(colour=await ctx.embed_color())
            embed.title = video_title
            embed.url = str(video_link)

            # TODO : figure out why tf it won't display embed thumbnail/image.
            embed.set_image(url=thumbnail)
            embed.set_footer(text=f"Page {i + 1} of {len(results)} | Uploaded: {created}")
            embed.description = duration + views + ratings
            pages.append(embed)

        if len(pages) == 1:
            return await ctx.send(pages[0])
        else:
            await menu(ctx, pages, DEFAULT_CONTROLS, timeout=60.0)

    @staticmethod
    def _time_diff(value1, value2, index: int):
        if value1 > value2:
            diff = relativedelta.relativedelta(value1, value2)
        else:
            diff = relativedelta.relativedelta(value2, value1)

        yrs = str(diff.years).zfill(2)
        mths = str(diff.months).zfill(2)
        days = str(diff.days).zfill(2)
        hrs = str(diff.hours).zfill(2)
        mins = str(diff.minutes).zfill(2)
        secs = str(diff.seconds).zfill(2)
        mu_secs = str(diff.microseconds)

        pretty = f"{yrs}y {mths}mo {days}d {hrs}h {mins}m {secs}s {mu_secs[:3]}μs"
        to_join = " ".join([x for x in pretty.split() if x[0:2] != "00"][:index])

        return to_join
