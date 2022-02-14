import asyncio
import random
from datetime import datetime

import aiohttp
import discord
from discord.ext import tasks
from redbot.core import commands, Config
from redbot.core.bot import Red


class RedditInfo(commands.Cog):
    """Fetch hot memes or info about Reddit account or subreddit."""

    __author__, __version__ = ("Author: ow0x", "Cog Version: 1.2.0")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\n{self.__author__}\n{self.__version__}"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.meme_subreddits = [
            "memes",
            "dankmemes",
            "meirl",
            "programmeranimemes",
            "bikinibottomtwitter",
            "2meirl4meirl",
        ]
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, 357059159021060097, force_registration=True)
        default_guild = {"channel_id": None}
        self.config.register_global(interval=5)
        self.config.register_guild(**default_guild)
        self._autopost_meme.start()

    async def initialize(self) -> None:
        delay = await self.config.interval()
        if delay != 5:
            self._autopost_meme.change_interval(minutes=delay)

    def cog_unload(self) -> None:
        asyncio.create_task(self.session.close())
        self._autopost_meme.cancel()

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    @tasks.loop(minutes=5)
    async def _autopost_meme(self) -> None:
        all_config = await self.config.all_guilds()
        for guild_id, guild_data in all_config.items():
            if guild_data["channel_id"] is None:
                continue

            guild = self.bot.get_guild(guild_id)
            channel = self.bot.get_channel(guild_data["channel_id"])
            bot_perms = channel.permissions_for(guild.me)
            if not (guild or channel or bot_perms.send_messages or bot_perms.embed_links):
                continue
            random_sub = random.choice(self.meme_subreddits)
            async with self.session.get(f"https://reddit.com/r/{random_sub}/hot.json") as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()

            await self._fetch_meme(data, channel)

    @_autopost_meme.before_loop
    async def _before_autopost_meme(self) -> None:
        await self.bot.wait_until_red_ready()

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def reddituser(self, ctx: commands.Context, username: str):
        """Fetch basic info about a Reddit user account."""
        await ctx.trigger_typing()
        async with self.session.get(f"https://reddit.com/user/{username}/about.json") as resp:
            if resp.status != 200:
                return await ctx.send(f"https://http.cat/{resp.status}")
            result = await resp.json()

        data = result.get("data")
        if data.get("is_suspended"):
            return await ctx.send("According to Reddit, that account has been suspended.")

        em = discord.Embed(colour=discord.Colour.random())
        username = data.get("display_name_prefixed")
        prefixed_name = f" ({username})" if username else ""
        em.set_author(
            name=f"{data.get('title') or data.get('name')}{prefixed_name}",
            icon_url="https://www.redditinc.com/assets/images/site/reddit-logo.png",
        )
        profile_url = f"https://reddit.com/user/{username}"
        if data.get("banner_img"):
            em.set_image(url=data["banner_img"].split("?")[0])
        em.set_thumbnail(url=str(data.get("icon_img")).split("?")[0])
        em.add_field(name="Account created:", value=f"<t:{int(data.get('created_utc'))}:R>")
        em.add_field(name="Total Karma:", value=f"{data.get('total_karma', 0):,}")
        extra_info = (
            f"Awardee Karma:  **{data.get('awardee_karma', 0):,}**\n"
            f"Awarder Karma:  **{data.get('awarder_karma', 0):,}**\n"
            f"Comment Karma:  **{data.get('comment_karma', 0):,}**\n"
            f"Link Karma:  **{data.get('link_karma', 0):,}**\n"
            f'has Reddit Premium?:  {"✅" if data.get("is_gold") else "❌"}\n'
            f'Verified Email?:  {"✅" if data.get("has_verified_email") else "❌"}\n'
            f'Is a subreddit mod?:  {"✅" if data.get("is_mod") else "❌"}\n'
        )
        if data.get("is_employee"):
            em.set_footer(text="\u2139  This user is a Reddit employee.")
        em.description = extra_info
        await ctx.send(profile_url, embed=em)

    @commands.command(aliases=("subinfo", "subrinfo"))
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def subredditinfo(self, ctx: commands.Context, subreddit: str, more_info: bool = False):
        """Fetch basic info about a subreddit.

        `more_info`: Shows some more info available for the subreddit. Defaults to False.
        """
        await ctx.trigger_typing()
        async with self.session.get(f"https://reddit.com/r/{subreddit}/about.json") as resp:
            if resp.status != 200:
                return await ctx.send(f"https://http.cat/{resp.status}")
            result = await resp.json()

        data = result.get("data")
        if data and data.get("dist") == 0:
            return await ctx.send("No results found for given subreddit name.")
        if data.get("over18") and not ctx.channel.is_nsfw():
            return await ctx.send("That subreddit is marked as NSFW. Try again in NSFW channel.")

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
            return "\u2705" if data.get(value) else "\u274C"

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
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def random_hot_meme(self, ctx: commands.Context):
        """Fetch a random hot meme, or a boring cringe one!"""
        await ctx.trigger_typing()
        random_sub = random.choice(self.meme_subreddits)
        async with self.session.get(f"https://reddit.com/r/{random_sub}/hot.json") as resp:
            if resp.status != 200:
                return await ctx.send(f"Reddit API returned {resp.status} HTTP status code.")
            data = await resp.json()
        await self._fetch_meme(data, ctx.channel, ctx=ctx)

    async def _fetch_subreddit_icon(self, subreddit: str) -> str:
        url = f"https://reddit.com/r/{subreddit}/about.json"
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return "https://i.imgur.com/DSBOK0P.png"
            meta = await resp.json()
        data = meta["data"]
        if not (data.get("icon_img") or data.get("community_icon")):
            return "https://i.imgur.com/DSBOK0P.png"
        return data.get("icon_img") or data.get("community_icon").split("?")[0]

    async def _fetch_meme(self, result, channel, **kwargs) -> None:
        ctx_or_channel = kwargs.get("ctx") or channel
        meme_array = result["data"]["children"]
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
            return await ctx_or_channel.send("NSFW meme found. Aborted in SFW channel.")

        img_types = ("jpg", "jpeg", "png", "gif")
        if (
            meme.get("is_video")
            or (meme.get("url") and "v.redd.it" in meme.get("url"))
            or (meme.get("url") and not meme.get("url").endswith(img_types))
        ):
            return await ctx_or_channel.send(meme.get("url"))
        emb = discord.Embed(colour=discord.Colour.random())
        emb.timestamp = datetime.utcfromtimestamp(int(meme["created_utc"]))
        emb.set_author(
            name=f'/r/{meme["subreddit"]}',
            icon_url=await self._fetch_subreddit_icon(meme["subreddit"]),
        )
        emb.title = meme.get("title", "")
        emb.description = f"This meme was posted <t:{int(meme['created_utc'])}:R>"
        emb.url = f"https://reddit.com{meme['permalink']}"
        emb.set_image(url=meme.get("url") or "")
        emb.set_footer(
            text=f"{meme.get('ups', 0):,} upvotes",
            icon_url="https://cdn.discordapp.com/emojis/752439401123938304.gif",
        )
        await ctx_or_channel.send(embed=emb)

    @commands.group()
    @commands.mod_or_permissions(manage_channels=True)
    async def automemeset(self, ctx: commands.Context):
        """Commands for auto meme posting in a channel."""
        pass

    @automemeset.command()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set a channel where random memes will be posted."""
        if channel is None:
            await self.config.guild(ctx.guild).channel_id.set(None)
            return await ctx.send("automeme channel is successfully removed/reset.")

        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        delay = await self.config.interval()
        await ctx.send(
            f"Channel is set. Memes will be auto posted every {delay} minutes to {channel.mention}."
        )
        await ctx.tick()

    @automemeset.command(hidden=True)
    async def force(self, ctx: commands.Context):
        """Force post the auto meme, to check if it's working or not."""
        await ctx.channel.trigger_typing()
        await self._autopost_meme.coro(self)
        await ctx.tick()

    @commands.is_owner()
    @automemeset.command()
    async def delay(self, ctx: commands.Context, minutes: int):
        """Specify the time delay in minutes after when meme will be posted in set channel.

        Minimum allowed value is 1 minute and max. is 1440 minutes (1 day). Default is 5 minutes.
        """
        delay = max(min(minutes, 1440), 1)
        self._autopost_meme.change_interval(minutes=delay)
        await self.config.interval.set(delay)
        await ctx.send(f"Memes will be auto posted every {delay} minutes from now!")
        await ctx.tick()
