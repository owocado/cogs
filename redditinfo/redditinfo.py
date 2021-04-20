import aiohttp
import io
import json
import re
import yarl

from datetime import datetime

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number


# All credits, rights and copyrights for below class code belongs to Rapptz (Danny#0007)
# Original source: https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/buttons.py#L68
# I do not claim any credits for this.
# The original LICENSE is available at https://github.com/Rapptz/RoboDanny/blob/rewrite/LICENSE.txt
class RedditMediaURL:
    VALID_PATH = re.compile(r'/r/[A-Za-z0-9_]+/comments/[A-Za-z0-9]+(?:/.+)?')

    def __init__(self, url):
        self.url = url
        self.filename = url.parts[1] + '.mp4'

    @classmethod
    async def convert(cls, ctx, argument):
        try:
            url = yarl.URL(argument)
        except Exception as e:
            raise commands.BadArgument('Not a valid URL.')

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'
        }
        await ctx.trigger_typing()
        if url.host == 'v.redd.it':
            # have to do a request to fetch the 'main' URL.
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    url = resp.url

        is_valid_path = url.host.endswith('.reddit.com') and cls.VALID_PATH.match(url.path)
        if not is_valid_path:
            raise commands.BadArgument('Not a reddit URL.')

        # Now we go the long way
        async with aiohttp.ClientSession() as session:
            async with session.get(url / '.json', headers=headers) as resp:
                if resp.status != 200:
                    raise commands.BadArgument(f'Reddit API failed with {resp.status}.')

                data = await resp.json()
                try:
                    submission = data[0]['data']['children'][0]['data']
                except (KeyError, TypeError, IndexError):
                    raise commands.BadArgument('Could not fetch submission.')

                try:
                    media = submission['media']['reddit_video']
                except (KeyError, TypeError):
                    try:
                        # maybe it's a cross post
                        crosspost = submission['crosspost_parent_list'][0]
                        media = crosspost['media']['reddit_video']
                    except (KeyError, TypeError, IndexError):
                        raise commands.BadArgument('Could not fetch media information.')

                try:
                    fallback_url = yarl.URL(media['fallback_url'])
                except KeyError:
                    raise commands.BadArgument('Could not fetch fall back URL.')

                return cls(fallback_url)


class RedditInfo(commands.Cog):
    """Fetch various info about Reddit user accounts and subreddits, or fetch a video from a reddit post."""

    __author__ = ["Rapptz (Danny#0007)", "឵឵❤#0055 (<@306810730055729152>)"]
    __version__ = "0.2.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def reddituser(self, ctx: commands.Context, user: str, details: bool = False):
        """Fetch basic info about a Reddit user account.

        `details`: Shows more information when set to `True`.
        Defaults to False.
        """
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://www.reddit.com/user/{user}/about.json") as response:
                    if response.status == 200:
                        data = json.loads(await response.read())
                    else:
                        return await ctx.send(f"Reddit API returned response code: https://http.cat/{response.status}")

            data = data.get("data")
            if data.get("is_suspended"):
                return await ctx.send("As per Reddit, that account has been suspended.")
            if not details:
                em = discord.Embed(colour=await ctx.embed_colour())
                em.title = data.get("subreddit").get("display_name_prefixed")
                em.url = f"https://reddit.com/user/{user}"
                if data.get("subreddit").get("banner_img") != "":
                    em.set_image(url=str(data.get("subreddit").get("banner_img")).split("?")[0])
                em.set_thumbnail(url=str(data.get("icon_img")).split("?")[0])
                cake_day = datetime.utcfromtimestamp(data.get("created_utc")).strftime('%b %d, %Y')
                em.add_field(name="Cake day", value=str(cake_day))
                em.add_field(name="Total Karma", value=humanize_number(str(data.get("total_karma"))))
            else:
                em = discord.Embed(colour=await ctx.embed_colour())
                em.title = data.get("subreddit").get("display_name_prefixed")
                em.url = f"https://reddit.com/user/{user}"
                em.description = data.get("subreddit").get("public_description")
                if data.get("subreddit").get("banner_img") != "":
                    em.set_image(url=str(data.get("subreddit").get("banner_img")).split("?")[0])
                em.set_thumbnail(url=str(data.get("icon_img")).split("?")[0])
                cake_day = datetime.utcfromtimestamp(data.get("created_utc")).strftime('%b %d, %Y')
                em.add_field(name="Cake day", value=str(cake_day))
                em.add_field(name="Total Karma", value=humanize_number(str(data.get("total_karma"))))
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
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def subrinfo(self, ctx: commands.Context, subr: str, details: bool = False):
        """Fetch basic info about an existing subreddit.

        `details`: Shows more information when set to `True`.
        Defaults to False.
        """
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://www.reddit.com/r/{subr}/about.json") as response:
                    if response.status == 200:
                        data = json.loads(await response.read())
                    else:
                        return await ctx.send(f"Reddit API returned response code: https://http.cat/{response.status}")

            if data.get("data", {}).get("dist", None) == 0:
                return await ctx.send("No results.")
            data = data.get("data")
            if data.get("over18") and not ctx.message.channel.is_nsfw():
                return await ctx.send("That subreddit is marked NSFW. Search aborted in SFW channel.")
            if not details:
                em = discord.Embed(colour=discord.Colour.random())
                em.title = data.get("url")
                em.url = f"https://reddit.com{data.get('url')}"
                em.description = data.get("public_description")
                if data.get("banner_img") != "":
                    em.set_image(url=str(data.get("banner_img")))
                if data.get("community_icon") != "":
                    em.set_thumbnail(url=str(data.get("community_icon")).split("?")[0])
                cake_day = datetime.utcfromtimestamp(data.get("created_utc")).strftime('%b %d, %Y')
                em.add_field(name="Created On", value=str(cake_day))
                em.add_field(name="Subscribers", value=humanize_number(str(data.get("subscribers"))))
                em.add_field(name="Active Users", value=humanize_number(str(data.get("active_user_count"))))
            else:
                em = discord.Embed(colour=discord.Colour.random())
                em.title = data.get("url")
                em.url = f"https://reddit.com{data.get('url')}"
                em.description = data.get("public_description")
                if data.get("banner_img") != "":
                    em.set_image(url=str(data.get("banner_img")))
                if data.get("community_icon") != "":
                    em.set_thumbnail(url=str(data.get("community_icon")).split("?")[0])
                cake_day = datetime.utcfromtimestamp(data.get("created_utc")).strftime('%b %d, %Y')
                em.add_field(name="Created On", value=str(cake_day))
                em.add_field(name="Subscribers", value=humanize_number(str(data.get("subscribers"))))
                em.add_field(name="Active Users", value=humanize_number(str(data.get("active_user_count"))))
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

    @commands.command()
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 15, commands.BucketType.member)
    async def vreddit(self, ctx: commands.Context, reddit_url: RedditMediaURL):
        """Downloads a v.redd.it submission.

        Regular reddit URLs or v.redd.it URLs are supported.
        """

        # This command and it's logic is imported from RoboDanny
        # https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/buttons.py#L401
        # to port for Red Discord bot cog compatibility.
        # All credits to Rapptz for providing this logic and source code.
        # I do not claim any credits or ownership for this command and it's respective logic.

        filesize = ctx.guild.filesize_limit if ctx.guild else 8388608
        async with aiohttp.ClientSession() as session:
            async with session.get(reddit_url.url) as resp:
                if resp.status != 200:
                    return await ctx.send('Could not download video.')

                if int(resp.headers['Content-Length']) >= filesize:
                    return await ctx.send('Video is too big to be uploaded.')

                data = await resp.read()
                await ctx.send(file=discord.File(io.BytesIO(data), filename=reddit_url.filename))
