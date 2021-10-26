import aiohttp
import random

from datetime import datetime

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number


class RedditInfo(commands.Cog):
    """Fetch hot memes or some info about Reddit user accounts and subreddits."""

    __author__ = "឵឵ow0x"
    __version__ = "0.3.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def reddituser(self, ctx: commands.Context, user: str, more_info: bool = False):
        """Fetch basic info about a Reddit user account.

        `more_info`: Shows more information when set to `True`.
        Defaults to False.
        """
        await ctx.trigger_typing()
        async with aiohttp.request("GET", f"https://old.reddit.com/user/{user}/about.json") as resp:
            if resp.status != 200:
                return await ctx.send(f"https://http.cat/{resp.status}")
            result = await resp.json()

        data = result.get("data")
        if data.get("is_suspended"):
            return await ctx.send("As per Reddit, that account has been suspended.")

        em = discord.Embed(colour=await ctx.embed_colour())
        em.title = data.get("subreddit").get("display_name_prefixed")
        em.url = f"https://reddit.com/user/{user}"
        if data.get("subreddit").get("banner_img") != "":
            em.set_image(url=str(data.get("subreddit").get("banner_img")).split("?")[0])
        em.set_thumbnail(url=str(data.get("icon_img")).split("?")[0])
        cake_day = datetime.utcfromtimestamp(data.get("created_utc")).strftime('%b %d, %Y')
        em.add_field(name="Cake day", value=str(cake_day))
        em.add_field(name="Total Karma", value=humanize_number(str(data.get("total_karma"))))
        if more_info:
            em.add_field(name="Awardee Karma", value=humanize_number(str(data.get("awardee_karma"))))
            em.add_field(name="Awarder Karma", value=humanize_number(str(data.get("awarder_karma"))))
            em.add_field(name="Comment Karma", value=humanize_number(str(data.get("comment_karma"))))
            em.add_field(name="Link Karma", value=humanize_number(str(data.get("link_karma"))))
            em.add_field(name="has Reddit Premium?", value="Yes" if data.get("is_gold") else "No")
            em.add_field(name="Verified Email?", value="Yes" if data.get("has_verified_email") else "No")
            em.add_field(name="Is a subreddit mod?", value="Yes" if data.get("is_mod") else "No")
            if data.get("is_employee"):
                em.set_footer(text="This user is a Reddit employee.")

        await ctx.send(embed=em)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def subrinfo(self, ctx: commands.Context, subr: str, more_info: bool = False):
        """Fetch basic info about an existing subreddit.

        `more_info`: Shows more information when set to `True`.
        Defaults to False.
        """
        await ctx.trigger_typing()
        async with aiohttp.request("GET", f"https://old.reddit.com/r/{subr}/about.json") as resp:
            if resp.status != 200:
                return await ctx.send(f"https://http.cat/{resp.status}")
            result = await resp.json()

        if result.get("data", {}).get("dist", None) == 0:
            return await ctx.send("No results.")
        data = result.get("data")
        if data.get("over18") and not ctx.channel.is_nsfw():
            return await ctx.send("That subreddit is marked NSFW. Search aborted in SFW channel.")

        em = discord.Embed(colour=discord.Colour.random())
        em.title = data.get("url")
        em.url = f"https://reddit.com{data.get('url')}"
        em.description = data.get("public_description")
        if data.get("banner_img") != "":
            em.set_image(url=data.get("banner_img") or "")
        if data.get("community_icon") != "":
            em.set_thumbnail(url=str(data.get("community_icon")).split("?")[0])
        cake_day = datetime.utcfromtimestamp(data.get("created_utc")).strftime('%b %d, %Y')
        em.add_field(name="Created On", value=str(cake_day))
        em.add_field(name="Subscribers", value=humanize_number(str(data.get("subscribers"))))
        em.add_field(name="Active Users", value=humanize_number(str(data.get("active_user_count"))))

        if more_info:
            em.add_field(name="Wiki enabled?", value="Yes" if data.get("wiki_enabled") else "No")
            em.add_field(name="Users can assign flairs?", value="Yes" if data.get("can_assign_user_flair") else "No")
            em.add_field(name="Galleries allowed?", value="Yes" if data.get("allow_galleries") else "No")
            em.add_field(name="Whether traffic statistics exposed to the public?", value="Yes" if data.get("public_traffic") else "No")
            em.add_field(name="ADS hidden by admin?", value="Yes" if data.get("hide_ads") else "No")
            em.add_field(name="Emojis enabled?", value="Yes" if data.get("emojis_enabled") else "No")
            em.add_field(name="Is community reviewed?", value="Yes" if data.get("community_reviewed") else "No")
            em.add_field(name="Spoilers enabled?", value="Yes" if data.get("spoilers_enabled") else "No")
            em.add_field(name="Discoverable?", value="Yes" if data.get("allow_discovery") else "No")
            em.add_field(name="Video uploads allowed?", value="Yes" if data.get("allow_videos") else "No")
            em.add_field(name="Image uploads allowed?", value="Yes" if data.get("allow_images") else "No")
            if data.get("submission_type") != "":
                em.add_field(name="Submissions type", value=data.get("submission_type"))
            if data.get("advertiser_category") != "":
                em.add_field(name="Advertiser category", value=data.get("advertiser_category"))
            if data.get("whitelist_status") != "":
                em.add_field(name="Advertising whitelist status", value=data.get("whitelist_status"))

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
        async with aiohttp.request("GET", f"https://old.reddit.com/r/{random_sub}/hot.json") as resp:
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
