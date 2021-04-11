import aiohttp
import json

from datetime import datetime

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number

class RedditInfo(commands.Cog):
	"""Fetch basic info about Reddit user accounts and subreddits."""

	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@commands.bot_has_permissions(embed_links=True)
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
				em.add_field(name="User has Reddit Premium?", value="Yes" if data.get("has_subscribed") else "No")
				em.add_field(name="Verified Email?", value="Yes" if data.get("has_verified_email") else "No")
				em.add_field(name="Accept Chats?", value="Yes" if data.get("accept_chats") else "No")
				em.add_field(name="Accept PMs?", value="Yes" if data.get("accept_pms") else "No")
				em.add_field(name="Is a subreddit mod?", value="Yes" if data.get("is_mod") else "No")
				if data.get("is_employee"):
					em.set_footer(text="This user is a Reddit employee.")

		await ctx.send(embed=em)

	@commands.command()
	@commands.bot_has_permissions(embed_links=True)
	async def subreddit(self, ctx: commands.Context, subr: str, details: bool = False):
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
			if data.get("primary_color") != "":
				color = data.get("primary_color")
			else:
				color = await ctx.embed_colour()
			if not details:
				em = discord.Embed(colour=color)
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
				em = discord.Embed(colour=color)
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
