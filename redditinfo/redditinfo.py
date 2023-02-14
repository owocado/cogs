import asyncio
import logging
import random
from datetime import datetime
from typing import Optional, Union

import aiohttp
import discord
from discord.ext import tasks
from redbot.core import Config, commands
from redbot.core.commands.context import Context
from redbot.core.bot import Red

from .handles import INTERESTING_SUBS, MEME_REDDITS

logger = logging.getLogger("red.owo.redditinfo")


class RedditInfo(commands.Cog):
    """Fetch hot memes or info about Reddit account or subreddit."""

    __authors__ = ["ow0x"]
    __version__ = "2.0.0"

    def format_help_for_context(self, ctx: Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(self.__authors__)}\n"
            f"**Cog version:**  v{self.__version__}"
        )

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, 357059159021060097, force_registration=True)
        default_guild = {"channel_id": None, "feed_channels": {}}
        self.config.register_channel(subreddit="")
        self.config.register_global(interval=5)
        self.config.register_guild(**default_guild)
        self._autopost_meme.start()
        self._fetch_random_post_task.start()

    async def cog_load(self) -> None:
        delay: int = await self.config.interval()
        if delay != 5:
            self._autopost_meme.change_interval(minutes=delay)
            self._fetch_random_post_task.change_interval(minutes=delay)

    async def cog_unload(self) -> None:
        await self.session.close()
        self._autopost_meme.cancel()
        self._fetch_random_post_task.cancel()

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    @tasks.loop(minutes=5)
    async def _fetch_random_post_task(self) -> None:
        all_data: dict = await self.config.all_channels()
        for channel_id, data in all_data.items():
            if not data["subreddit"]:
                continue
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                logger.info(f"Channel or thread by ID: {channel_id} could not be found!")
                continue
            bot_perms = channel.permissions_for(channel.guild.me)
            if not bot_perms.send_messages:
                logger.info(
                    f"Missing send messages permission in {channel} (ID: {channel.id})"
                )
                continue
            try:
                async with self.session.get(
                    f"https://old.reddit.com/r/{data['subreddit']}/random.json"
                ) as resp:
                    if resp.status != 200:
                        logger.info(f"Reddit sent non 2xx response code: {resp.status}")
                        continue
                    random_feeds = await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                logger.exception(f"Error while fetching hot meme from Reddit!", exc_info=True)
                continue
            try:
                random_post: dict = random_feeds[0]["data"]["children"][0]["data"]
                interval: int = await self.config.interval()
                next_when = f"next post <t:{int(discord.utils.utcnow().timestamp()) + interval*60}:R>"
                await channel.send(f"https://www.rxyddit.com{random_post['permalink']} | {next_when}")
            except Exception as exc:
                logger.exception("Error sending random auto post", exc_info=exc)
                continue

    @_fetch_random_post_task.before_loop
    async def _before_fetch_random_post_task(self) -> None:
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=5)
    async def _autopost_meme(self) -> None:
        data = None
        all_config = await self.config.all_guilds()
        for guild_id, guild_data in all_config.items():
            if guild_data["channel_id"] is None:
                continue

            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                logger.info(f"Guild by ID: {guild_id} could not be found!")
                continue
            channel = guild.get_channel_or_thread(guild_data["channel_id"])
            if not channel:
                logger.info(
                    f"Channel or thread by ID: {guild_data['channel_id']} could not be found!"
                )
                continue
            bot_perms = channel.permissions_for(guild.me)
            if not bot_perms.send_messages or not bot_perms.embed_links:
                logger.info(
                    f"Missing send messages or embed links perms in {channel} (ID: {channel.id})"
                )
                continue
            random_sub = random.choice(MEME_REDDITS)
            try:
                async with self.session.get(
                    f"https://reddit.com/r/{random_sub}/hot.json?limit=10"
                ) as resp:
                    if resp.status != 200:
                        logger.info(f"Reddit sent non 2xx response code: {resp.status}")
                        continue
                    data = await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                logger.exception(f"Error while fetching hot meme from Reddit!", exc_info=True)
                continue

            embed = await self._fetch_random_post(data, channel)
            if not embed:
                logger.info("Could not generate embed for autopost meme feed!")
                continue
            await channel.send(embed=embed)

    @_autopost_meme.before_loop
    async def _before_autopost_meme(self) -> None:
        await self.bot.wait_until_ready()

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def reddituser(self, ctx: Context, username: str):
        """Fetch basic info about a Reddit user account."""
        async with ctx.typing():
            try:
                async with self.session.get(
                    f"https://reddit.com/user/{username}/about.json"
                ) as resp:
                    if resp.status != 200:
                        return await ctx.send(f"https://http.cat/{resp.status}")
                    result = await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                return await ctx.send("Operation timeout. Try again later.")

            data = result.get("data")
            if data.get("is_suspended"):
                return await ctx.send("According to Reddit, that account has been suspended.")

            em = discord.Embed(colour=discord.Colour.random())
            em.set_author(
                name=data.get("name"),
                icon_url="https://www.redditinc.com/assets/images/site/reddit-logo.png",
            )
            profile_url = f"https://reddit.com/user/{data.get('name') or username}"
            if data.get("banner_img"):
                em.set_image(url=data["banner_img"].split("?")[0])
            em.set_thumbnail(url=data.get("icon_img") or "")
            em.add_field(name="Account created:", value=f"<t:{int(data.get('created_utc'))}:R>")
            em.add_field(name="Total Karma:", value=f"{data.get('total_karma', 0):,}")
            extra_info = (
                f"Awardee Karma:  **{data.get('awardee_karma', 0):,}**\n"
                f"Awarder Karma:  **{data.get('awarder_karma', 0):,}**\n"
                f"Comment Karma:  **{data.get('comment_karma', 0):,}**\n"
                f"Link Karma:  **{data.get('link_karma', 0):,}**\n"
                f'has Reddit Premium?:  {"`✅` Yes" if data.get("is_gold") else "`❌` No"}\n'
                f'Verified Email?:  {"`✅` Yes" if data.get("has_verified_email") else "`❌` No"}\n'
                f'Is a subreddit mod?:  {"`✅` Yes" if data.get("is_mod") else "`❌` No"}\n'
            )
            if data.get("is_employee"):
                em.set_footer(text="ℹ  This user is a Reddit employee.")
            em.description = extra_info
        await ctx.send(profile_url, embed=em)

    @commands.command(aliases=("subinfo", "subrinfo"))
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def subredditinfo(self, ctx: Context, subreddit: str, more_info: bool = False):
        """Fetch basic info about a subreddit.

        `more_info`: Shows some more info available for the subreddit. Defaults to False.
        """
        async with ctx.typing():
            try:
                async with self.session.get(f"https://reddit.com/r/{subreddit}/about.json") as resp:
                    if resp.status != 200:
                        return await ctx.send(f"https://http.cat/{resp.status}")
                    result = await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                return await ctx.send("Operation timeout. Try again later.")

            data = result.get("data")
            if data and data.get("dist") == 0:
                return await ctx.send("No subreddits were found from given name.")
            if data.get("over18") and not ctx.channel.is_nsfw():
                await ctx.send("That subreddit is marked as NSFW. Try again in NSFW channel.")
                return

            em = discord.Embed(colour=discord.Colour.random())
            em.set_author(name=data.get("url"), icon_url=data.get("icon_img") or "")
            subreddit_link = f"https://reddit.com{data.get('url')}"
            em.description = f"**{data.get('title', '')}**\n\n{data.get('public_description', '')}"
            if data.get("banner_img"):
                em.set_image(url=data["banner_img"])
            if data.get("community_icon"):
                em.set_thumbnail(url=data["community_icon"].split("?")[0])
            em.add_field(name="Created On", value=f"<t:{int(data.get('created_utc'))}:R>")
            em.add_field(name="Subscribers", value=f"{data.get('subscribers', 0):,}")
            em.add_field(name="Active Users", value=f"{data.get('active_user_count', 0):,}")

            def yes_no(value: str) -> str:
                return "✅ Yes" if data.get(value) else "❌ No"

            extra_info = ""
            if more_info:
                extra_info += (
                    f"Wiki enabled?:  {yes_no('wiki_enabled')}\n"
                    f"Users can assign flairs?:  {yes_no('can_assign_user_flair')}\n"
                    f"Galleries allowed?:  {yes_no('allow_galleries')}\n"
                    f"Is traffic stats exposed to public?:  {yes_no('public_traffic')}\n"
                    f"ADS hidden by admin?:  {yes_no('hide_ads')}\n"
                    f"Emojis enabled?:  {yes_no('emojis_enabled')}\n"
                    f"Is community reviewed?:  {yes_no('community_reviewed')}\n"
                    f"Spoilers enabled?:  {yes_no('spoilers_enabled')}\n"
                    f"Discoverable?:  {yes_no('allow_discovery')}\n"
                    f"Video uploads allowed?:  {yes_no('allow_videos')}\n"
                    f"Image uploads allowed?:  {yes_no('allow_images')}\n"
                )
                if data.get("submission_type"):
                    extra_info += "Submissions type:  " + data["submission_type"] + "\n"
                if data.get("advertiser_category"):
                    extra_info += "Advertiser category:  " + data["advertiser_category"] + "\n"
                if data.get("whitelist_status"):
                    extra_info += "Advertising whitelist status:  " + data["whitelist_status"] + "\n"
            if extra_info:
                em.add_field(name="(Extra) Misc. Info:", value=extra_info, inline=False)
        await ctx.send(subreddit_link, embed=em)

    @commands.command(name="meme")
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def random_hot_meme(self, ctx: Context):
        """Fetch a random hot meme, or a boring cringe one!"""
        async with ctx.typing():
            random_sub = random.choice(MEME_REDDITS)
            try:
                async with self.session.get(
                    f"https://reddit.com/r/{random_sub}/hot.json?limit=20"
                ) as resp:
                    if resp.status != 200:
                        return await ctx.send(f"https://http.cat/{resp.status}.jpg")
                    data = await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                return await ctx.send("Operation timeout. Try again later.")

        embed = await self._fetch_random_post(data, ctx.channel, ctx=ctx)
        if not embed:
            return
        await ctx.send(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def interesting(self, ctx: Context):
        """Responds with random interesting reddit post."""
        random_sub = random.choice(INTERESTING_SUBS)
        async with ctx.typing():
            try:
                async with self.session.get(
                    f"https://reddit.com/r/{random_sub}/hot.json?limit=10"
                ) as resp:
                    if resp.status != 200:
                        return await ctx.send(f"https://http.cat/{resp.status}.jpg")
                    data = await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                return await ctx.send("Operation timeout. Try again later.")

        embed = await self._fetch_random_post(data, ctx.channel, ctx=ctx)
        if not embed:
            return
        await ctx.send(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def subreddit(self, ctx: Context, subreddit_name: str):
        """Fetch a random hot post entry from the given subreddit."""
        async with ctx.typing():
            params = {
                "utm_campaign": "redirect",
                "utm_source": "reddit",
                "utm_medium": "desktop",
                "utm_name": "random_link"
            }
            try:
                async with self.session.get(
                    f"https://reddit.com/r/{subreddit_name}/.json",
                    params=params
                ) as resp:
                    if resp.status != 200:
                        return await ctx.send(f"https://http.cat/{resp.status}.jpg")
                    data = await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                return await ctx.send("Operation timeout. Try again later.")

        embed = await self._fetch_random_post(data, ctx.channel, ctx=ctx)
        if not embed:
            return
        await ctx.send(embed=embed)

    async def _fetch_subreddit_icon(self, subreddit: str) -> str:
        url = f"https://reddit.com/r/{subreddit}/about.json"
        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return "https://i.imgur.com/DSBOK0P.png"
                data = (await resp.json()).get("data") or {}
                if not (data.get("icon_img") or data.get("community_icon")):
                    return "https://i.imgur.com/DSBOK0P.png"
                return data.get("icon_img") or data.get("community_icon").split("?")[0]
        except (AttributeError, aiohttp.ClientError, asyncio.TimeoutError):
            return "https://i.imgur.com/DSBOK0P.png"

    async def _fetch_random_post(self, result: dict, channel, **kwargs) -> Optional[discord.Embed]:
        ctx_or_channel = kwargs.get("ctx") or channel
        meme_array = result.get("data", {}).get("children", [])
        if not meme_array:
            await ctx_or_channel.send("Sad trombone. No results found!")
            return None

        random_index = random.randint(0, len(meme_array) - 1)
        meme = meme_array[random_index]["data"]
        # make 3 attemps if nsfw meme found in sfw channel, shittalkers go brrr
        if meme.get("over_18") and not channel.is_nsfw():
            meme = meme_array[random.randint(0, len(meme_array) - 1)]["data"]
        # retrying again to get a sfw meme
        if meme.get("over_18") and not channel.is_nsfw():
            meme = meme_array[random.randint(0, len(meme_array) - 1)]["data"]
        # retrying last time to get sfw meme
        if meme.get("over_18") and not channel.is_nsfw():
            meme = meme_array[random.randint(0, len(meme_array) - 1)]["data"]
        if meme.get("over_18") and not channel.is_nsfw():
            await ctx_or_channel.send("NSFW meme found. Aborted in SFW channel.")
            return None

        img_types = ("jpg", "jpeg", "png", "gif")
        if (
            meme.get("is_video")
            or (meme.get("url") and "v.redd.it" in meme.get("url"))
            or (meme.get("url") and not meme.get("url").endswith(img_types))
        ):
            await ctx_or_channel.send(f"https://reddit.com{meme.get('permalink', '')}")
            return None
        emb = discord.Embed(colour=discord.Colour.random())
        emb.timestamp = datetime.utcfromtimestamp(int(meme["created_utc"]))
        emb.set_author(
            name=f'/r/{meme["subreddit"]}',
            icon_url=await self._fetch_subreddit_icon(meme["subreddit"]),
        )
        emb.title = meme.get("title", "")
        emb.description = f"This was posted <t:{int(meme['created_utc'])}:R>"
        emb.url = f"https://reddit.com{meme['permalink']}"
        emb.set_image(url=meme.get("url") or "")
        emb.set_footer(
            text=f"{meme.get('ups', 0):,} upvotes",
            icon_url="https://cdn.discordapp.com/emojis/752439401123938304.gif",
        )
        return emb

    @commands.group()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.mod_or_permissions(manage_channels=True)
    async def randomfeedset(self, ctx: Context):
        """Command group to autopost random post from a subreddit."""
        pass

    @randomfeedset.command()
    async def add(
        self,
        ctx: Context,
        subreddit: str,
        channel: Union[discord.TextChannel, discord.Thread] = commands.CurrentChannel,
    ):
        """Set up a channel where random post from given subreddit will be posted on given interval in minutes.

        Provide the valid subreddit name without `/r/` prefix or any formatting.
        """
        await ctx.typing()
        try:
            async with self.session.get(f"https://reddit.com/r/{subreddit}/about.json") as resp:
                if resp.status != 200:
                    return await ctx.send(f"https://http.cat/{resp.status}")
                result = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return await ctx.send(
                "Timeout while trying to query subreddit by given name. Try again later."
            )

        data = result.get("data")
        if data and data.get("dist") == 0:
            return await ctx.send("No subreddits were found from given name.")
        if data.get("over18") and not ctx.channel.is_nsfw():
            await ctx.send("That subreddit is marked as NSFW. Try again in NSFW channel.")
            return
        current_feed = await self.config.channel(channel).subreddit()
        if current_feed and current_feed == subreddit:
            await ctx.send("There is already a feed setup for that subreddit in this channel.")
            return

        await self.config.channel(channel).subreddit.set(subreddit)
        await ctx.send(
            f"✅ Done. Random posts from `/{data['display_name_prefixed']}` will be "
            f"posted in {channel.mention} at already specified interval.\n"
            f"Use `{ctx.clean_prefix}randomfeedset interval` cmd to change delay timer."
        )
        await ctx.tick()

    @randomfeedset.command(aliases=["delay", "timer"])
    async def interval(self, ctx: Context, minutes: int):
        """Specify the interval in minutes after for random auto post.

        Allowed interval is from 1 to 1440 minutes (1 day). Default is 5 minutes.
        """
        delay = max(min(minutes, 1440), 1)
        self._autopost_meme.change_interval(minutes=delay)
        self._fetch_random_post_task.change_interval(minutes=delay)
        await self.config.interval.set(delay)
        await ctx.send(f"✅ Done. Changed interval for auto post feed to {delay} minutes!")
        await ctx.tick()

    @randomfeedset.command()
    async def remove(
        self,
        ctx: Context,
        channel: Union[discord.TextChannel, discord.Thread] = commands.CurrentChannel
    ):
        """Removes any existing feed setup for a channel or thread."""
        current_feed = await self.config.channel(channel).subreddit()
        if not current_feed:
            await ctx.send(f"There is no random post feed setup for {channel.mention}!")
            return

        await self.config.channel(channel).subreddit.set(None)
        await ctx.send(
            f"Done. Feed `/r/{current_feed}` has been removed from {channel.mention}!\n"
            "Hence, random posts from that subreddit will no longer be posted."
        )
        await ctx.tick()

    @commands.group()
    @commands.guild_only()
    @commands.mod_or_permissions(manage_channels=True)
    async def automemeset(self, ctx: Context):
        """Commands for auto meme posting in a channel."""
        pass

    @automemeset.command()
    async def channel(self, ctx: Context, channel: Union[discord.TextChannel, discord.Thread] = None):
        """Set a channel where random memes will be posted."""
        if channel is None:
            await self.config.guild(ctx.guild).channel_id.set(None)
            return await ctx.send("automeme channel is successfully removed/reset.")

        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        delay = await self.config.interval()
        await ctx.send(
            "Channel is set. Memes will be auto posted "
            f"every {delay} minutes to {channel.mention}."
        )
        await ctx.tick()

    @automemeset.command(hidden=True)
    async def force(self, ctx: Context):
        """Force post the auto meme, to check if it's working or not."""
        await self._autopost_meme.coro(self)
        await ctx.tick()

    @commands.is_owner()
    @automemeset.command()
    async def delay(self, ctx: Context, minutes: int):
        """Specify the interval in minutes after when meme will be posted in set channel.

        Allowed interval is from 1 to 1440 minutes (1 day). Default is 5 minutes.
        """
        delay = max(min(minutes, 1440), 1)
        self._autopost_meme.change_interval(minutes=delay)
        self._fetch_random_post_task.change_interval(minutes=delay)
        await self.config.interval.set(delay)
        await ctx.send(f"✅ Done. Changed interval for auto post feed to {delay} minutes!")
        await ctx.tick()
