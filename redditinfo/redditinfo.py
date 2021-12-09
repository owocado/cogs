import asyncio
import random

from datetime import datetime

import aiohttp
import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_number


class RedditInfo(commands.Cog):
    """Fetch hot memes or some info about Reddit user accounts and subreddits."""

    __author__ = "ow0x"
    __version__ = "1.0.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot: Red):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, 357059159021060097, force_registration=True)

    def cog_unload(self) -> None:
        asyncio.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def reddituser(self, ctx: commands.Context, username: str, more_info: bool = False):
        """Fetch basic info about a Reddit user account.

        `more_info`: Shows more information when set to `True`. Defaults to False.
        """
        await ctx.trigger_typing()
        async with self.session.get(f"https://old.reddit.com/user/{username}/about.json") as resp:
            if resp.status != 200:
                return await ctx.send(f"https://http.cat/{resp.status}")
            result = await resp.json()

        data = result.get("data")
        if data.get("is_suspended"):
            return await ctx.send("As per Reddit, that account has been suspended.")

        em = discord.Embed(colour=await ctx.embed_colour())
        em.set_author(
            name=f"{data.get('subreddit', {}).get('title') or data.get('name')} ({data.get('subreddit', {}).get('display_name_prefixed')})",
            icon_url="https://www.redditinc.com/assets/images/site/reddit-logo.png",
        )
        profile_url = f"https://reddit.com/user/{username}"
        if data.get("subreddit", {}).get("banner_img", "") != "":
            em.set_image(url=data["subreddit"]["banner_img"].split("?")[0])
        em.set_thumbnail(url=str(data.get("icon_img")).split("?")[0])
        em.add_field(name="Account created:", value=f"<t:{int(data.get('created_utc'))}:R>")
        em.add_field(name="Total Karma:", value=humanize_number(str(data.get("total_karma"))))
        extra_info = ""
        if more_info:
            extra_info += "**Awardee Karma:**  " + humanize_number(str(data.get("awardee_karma", 0))) + "\n"
            extra_info += "**Awarder Karma:**  " + humanize_number(str(data.get("awarder_karma", 0))) + "\n"
            extra_info += "**Comment Karma:**  " + humanize_number(str(data.get("comment_karma", 0))) + "\n"
            extra_info += "**Link Karma:**  " + humanize_number(str(data.get("link_karma", 0))) + "\n"
            extra_info += "**has Reddit Premium?:**  " + ("✅" if data.get("is_gold") else "❌") + "\n"
            extra_info += "**Verified Email?:**  " + ("✅" if data.get("has_verified_email") else "❌") + "\n"
            extra_info += "**Is a subreddit mod?:**  " + ("✅" if data.get("is_mod") else "❌") + "\n"
            if data.get("is_employee"):
                em.set_footer(text="This user is a Reddit employee.")
        em.description = extra_info
        await ctx.send(profile_url, embed=em)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def subrinfo(self, ctx: commands.Context, subreddit: str, more_info: bool = False):
        """Fetch basic info about an existing subreddit.

        `more_info`: Shows more information when set to `True`. Defaults to False.
        """
        await ctx.trigger_typing()
        async with self.session.get(f"https://old.reddit.com/r/{subreddit}/about.json") as resp:
            if resp.status != 200:
                return await ctx.send(f"https://http.cat/{resp.status}")
            result = await resp.json()

        data = result.get("data")
        if data and data.get("dist", 0) == 0:
            return await ctx.send("No results found for given subreddit name.")
        if data.get("over18") and not ctx.channel.is_nsfw():
            return await ctx.send("That subreddit is marked NSFW. Search aborted in SFW channel.")

        em = discord.Embed(colour=discord.Colour.random())
        em.title = data.get("url")
        em.url = f"https://reddit.com{data.get('url')}"
        em.description = data.get("public_description", "")
        if data.get("banner_img", "") != "":
            em.set_image(url=data.get("banner_img", ""))
        if data.get("community_icon", "") != "":
            em.set_thumbnail(url=data["community_icon"].split("?")[0])
        em.add_field(name="Created On", value=f"<t:{int(data.get('created_utc'))}:R>")
        em.add_field(name="Subscribers", value=humanize_number(str(data.get("subscribers"))))
        em.add_field(name="Active Users", value=humanize_number(str(data.get("active_user_count"))))

        extra_info = ""
        if more_info:
            extra_info += "**Wiki enabled?:**  " + ("✅" if data.get("wiki_enabled") else "❌") + "\n"
            extra_info += "**Users can assign flairs?:**  " + ("✅" if data.get("can_assign_user_flair") else "❌") + "\n"
            extra_info += "**Galleries allowed?:**  " + ("✅" if data.get("allow_galleries") else "❌") + "\n"
            extra_info += "**Is traffic stats exposed to public?:**  " + ("✅" if data.get("public_traffic") else "❌") + "\n"
            extra_info += "**ADS hidden by admin?:**  " + ("✅" if data.get("hide_ads") else "❌") + "\n"
            extra_info += "**Emojis enabled?:**  " + ("✅" if data.get("emojis_enabled") else "❌") + "\n"
            extra_info += "**Is community reviewed?:**  " + ("✅" if data.get("community_reviewed") else "❌") + "\n"
            extra_info += "**Spoilers enabled?:**  " + ("✅" if data.get("spoilers_enabled") else "❌") + "\n"
            extra_info += "**Discoverable?:**  " + ("✅" if data.get("allow_discovery") else "❌") + "\n"
            extra_info += "**Video uploads allowed?:**  " + ("✅" if data.get("allow_videos") else "❌") + "\n"
            extra_info += "**Image uploads allowed?:**  " + ("✅" if data.get("allow_images") else "❌") + "\n"
            if data.get("submission_type", "") != "":
                extra_info += "**Submissions type:**  " + data["submission_type"] + "\n"
            if data.get("advertiser_category", "") != "":
                extra_info += "**Advertiser category:**  " + data["advertiser_category"] + "\n"
            if data.get("whitelist_status", "") != "":
                extra_info += "**Advertising whitelist status:**  " + data["whitelist_status"] + "\n"
        em.add_field(name="(Extra) Misc. Info:", value=extra_info, inline=False)
        await ctx.send(embed=em)

    @commands.command(name="rmeme")
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def random_hot_meme(self, ctx: commands.Context):
        """Fetch a random hot meme, or a boring cringe one, I suppose!"""
        await ctx.trigger_typing()
        meme_subreddits = [
            "memes",
            "dankmemes",
            "gamingcirclejerk",
            "meirl",
            "programmerhumor",
            "programmeranimemes",
        ]
        random_sub = random.choice(meme_subreddits)
        async with self.session.get(f"https://old.reddit.com/r/{random_sub}/hot.json") as resp:
            if resp.status != 200:
                return await ctx.send(f"Reddit API returned {resp.status} HTTP status code.")
            result = await resp.json()

        meme_array = result["data"]["children"]
        random_index = random.randint(0, len(meme_array) - 1)
        random_meme = meme_array[random_index]["data"]
        # make 3 attemps if nsfw meme found in sfw channel, shittalkers go brrr
        if random_meme.get("over_18") and not ctx.channel.is_nsfw():
            random_meme = meme_array[random.randint(0, len(meme_array) - 1)]["data"]
        # retrying again to get a sfw meme
        if random_meme.get("over_18") and not ctx.channel.is_nsfw():
            random_meme = meme_array[random.randint(0, len(meme_array) - 1)]["data"]
        # retrying last time to get sfw meme
        if random_meme.get("over_18") and not ctx.channel.is_nsfw():
            return await ctx.send("NSFW meme found. Aborted in SFW channel. Please try again.")

        img_types = ('jpg', "jpeg", 'png', 'gif')
        if (
            random_meme.get("is_video")
            or (random_meme.get("url") and "v.redd.it" in random_meme.get("url"))
            or (random_meme.get("url") and not random_meme.get("url").endswith(img_types))
        ):
            return await ctx.send(
                "This meme is a video(?) type, which cannot be previewed in fancy "
                f"embed, so here is it's direct link:\n{random_meme.get('url')}"
            )
        emb = discord.Embed(colour=discord.Colour.random())
        emb.title = random_meme.get("title", "None")
        emb.url = f"https://old.reddit.com{random_meme['permalink']}"
        emb.set_image(url=random_meme.get("url"))
        emb.set_footer(
            text=f"{random_meme.get('ups')} upvotes • From /r/{random_meme.get('subreddit')}",
            icon_url="https://cdn.discordapp.com/emojis/752439401123938304.gif",
        )
        await ctx.send(embed=emb)
