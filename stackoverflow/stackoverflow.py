import aiohttp
import asyncio

from datetime import datetime
from html import unescape
from typing import Optional

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number, pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

BASE_API_URL = "http://api.stackexchange.com/2.2/search/advanced"


class StackOverflow(commands.Cog):
    """A cog to search your query on StackOverflow and other Stack Exchange Network domains."""

    __author__ = "<@306810730055729152>"
    __version__ = "0.1.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.stackexchange_networks = [
            "academia",
            "ai",
            "android",
            "anime",
            "api",
            "apple",
            "arduino",
            "astronomy",
            "biology",
            "bitcoin",
            "blender",
            "boardgames",
            "chemistry",
            "chess",
            "chinese",
            "codegolf",
            "codereview",
            "cooking",
            "crypto",
            "cs",
            "cstheory",
            "data",
            "datascience",
            "dba",
            "diy",
            "drupal",
            "dsp",
            "earthscience",
            "economics",
            "electronics",
            "emacs",
            "english",
            "ethereum",
            "expressionengine",
            "fitness",
            "french",
            "gamedev",
            "garderning",
            "german",
            "gis",
            "graphicdesign",
            "hardwarerecs",
            "history",
            "japanese",
            "law",
            "linguistics",
            "math",
            "mathematica",
            "meta",
            "money",
            "movies",
            "music",
            "networkengineering",
            "outdoors",
            "photo",
            "physics",
            "poker",
            "psychology",
            "raspberrypi",
            "rpg",
            "russian",
            "salesforce",
            "scicomp",
            "scifi",
            "security",
            "sharepoint",
            "softwareengineering",
            "softwarerecs",
            "sound",
            "spanish",
            "sports",
            "sqa",
            "tex",
            "unix",
            "ux",
            "video",
            "webapps",
            "webmasters",
            "wordpress",
            "worldbuilding",
        ]

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def stackoverflow(self, ctx: commands.Context, *, query: str):
        """Returns link(s) to related stackoverflow question articles based on your query.

        Also shows some basic stats about said question article."""
        api_key = (await ctx.bot.get_shared_api_tokens("stackexchange")).get("api_key")
        api_key = api_key if api_key else ""

        params = {
            "order": "asc",
            "sort": "relevance",
            "q": query,
            "key": api_key,
            "site": "stackoverflow",
        }
        async with ctx.typing():
            try:
                async with self.session.get(BASE_API_URL, params=params) as response:
                    if response.status == 200:
                        items = await response.json()
                    else:
                        return await ctx.send(f"https://http.cat/{response.status}")
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            if items.get("quota_remaining") == 0:
                return await ctx.send(
                    "You have exhausted your daily API calls quota. Please try again tomorrow."
                )
            if len(items.get("items")) == 0:
                return await ctx.send("No results")
            embed_list = []
            for data in items.get("items"):
                em = discord.Embed(color=await ctx.embed_colour())
                em.title = unescape(data.get("title", "None"))
                em.url = data.get("link")
                if data.get("accepted_answer_id") is not None:
                    em.description = f"**Accepted answer**: https://stackoverflow.com/a/{data.get('accepted_answer_id')}"
                question_owner = (
                    "["
                    + unescape(data.get("owner").get("display_name", "Unknown"))
                    + "]("
                    + data.get("owner").get("link")
                    + ")"
                )
                em.add_field(name="Asked by", value=question_owner)
                em.add_field(name="Tags", value=", ".join(data.get("tags")))
                created_on = datetime.utcfromtimestamp(data.get("creation_date"))
                since_created = (ctx.message.created_at - created_on).days
                em.add_field(
                    name="Question asked on",
                    value=f"{created_on.strftime('%d %b, %Y')} ({since_created} days ago)",
                    inline=False,
                )
                if data.get("last_edit_date") is not None:
                    edited_on = datetime.utcfromtimestamp(data.get("last_edit_date"))
                    edited_since = (ctx.message.created_at - edited_on).days
                    revisions = f"[{edited_since} days ago](https://stackoverflow.com/posts/{data.get('question_id')}/revisions)"
                    em.add_field(
                        name="Question last edited on",
                        value=f"{edited_on.strftime('%d %b, %Y')} ({revisions})",
                        inline=False,
                    )
                recent_activity_on = datetime.utcfromtimestamp(
                    data.get("last_activity_date")
                )
                since_activity = (ctx.message.created_at - recent_activity_on).days
                em.add_field(
                    name="Last activity on",
                    value=f"{recent_activity_on.strftime('%d %b, %Y')} ({since_activity} days ago)",
                    inline=False,
                )
                if data.get("score") > 0:
                    score = f"Question score: {humanize_number(data.get('score'))}"
                if data.get("view_count") > 0:
                    views = f"Views: {humanize_number(data.get('view_count'))}"
                if data.get("answer_count") > 0:
                    answers = f"Answers: {humanize_number(data.get('answer_count'))}"
                em.set_footer(
                    text=f"{score} | {views} | {answers} | Content license: {data.get('content_license', 'None')}"
                )
                embed_list.append(em)

        if not embed_list:
            return await ctx.send("No results.")
        elif len(embed_list) == 1:
            return await ctx.send(embed=embed_list[0])
        else:
            await menu(ctx, embed_list, DEFAULT_CONTROLS, timeout=60.0)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def stackexchange(self, ctx: commands.Context, subdomain: str, *, query: str):
        """Search for your query on any of stackexchange domain sites.

        Valid stackexchange network subdomains are:
        `academia`, `ai`, `android`, `anime`, `api`, `apple`, `arduino`, `astronomy`, `biology`, `bitcoin`, `blender`, `boardgames`, `chemistry`, `chess`, `chinese`, `codegolf`, `codereview`, `cooking`, `crypto`, `cs`, `cstheory`, `data`, `datascience`, `dba`, `diy`, `drupal`, `dsp`, `earthscience`, `economics`, `electronics`, `emacs`, `english`, `ethereum`, `expressionengine`, `fitness`, `french`, `gamedev`, `garderning`, `german`, `gis`, `graphicdesign`, `hardwarerecs`, `history`, `japanese`, `law`, `linguistics`, `math`, `mathematica`, `meta`, `money`, `movies`, `music`, `networkengineering`, `outdoor`, `photos`, `physics`, `poker`, `psychology`, `raspberrypi`, `rpg`, `russian`, `salesforce`, `scicomp`, `scifi`, `security`, `sharepoint`, `softwareengineering`, `softwarerecs`, `sound`, `spanish`, `sports`, `sqa`, `tex`, `unix`, `ux`, `video`, `webapps`, `webmasters`, `wordpress`, `worldbuilding`
        """
        if subdomain not in self.stackexchange_networks:
            return await ctx.send(
                "That is not a valid stackexchange site. See the command help to see available ones."
            )
        api_key = (await ctx.bot.get_shared_api_tokens("stackexchange")).get("api_key")
        api_key = api_key if api_key else ""

        params = {
            "order": "asc",
            "sort": "relevance",
            "q": query,
            "key": api_key,
            "site": subdomain,
        }

        async with ctx.typing():
            try:
                async with self.session.get(BASE_API_URL, params=params) as response:
                    if response.status == 200:
                        items = await response.json()
                    else:
                        return await ctx.send(f"https://http.cat/{response.status}")
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            if items.get("quota_remaining") == 0:
                return await ctx.send(
                    "You have exhausted your daily API calls quota. Please try again tomorrow."
                )
            if len(items.get("items")) == 0:
                return await ctx.send("No results")
            embed_list = []
            for data in items.get("items"):
                em = discord.Embed(color=await ctx.embed_colour())
                em.title = unescape(data.get("title", "None"))
                em.url = data.get("link")
                if data.get("accepted_answer_id") is not None:
                    em.description = f"**Accepted answer**: https://{subdomain}.stackexchange.com/a/{data.get('accepted_answer_id')}"
                question_owner = (
                    "["
                    + unescape(data.get("owner").get("display_name", "Unknown"))
                    + "]("
                    + data.get("owner").get("link")
                    + ")"
                )
                em.add_field(name="Asked by", value=question_owner)
                em.add_field(name="Tags", value=", ".join(data.get("tags")))
                created_on = datetime.utcfromtimestamp(data.get("creation_date"))
                since_created = (ctx.message.created_at - created_on).days
                em.add_field(
                    name="Question asked on",
                    value=f"{created_on.strftime('%d %b, %Y')} ({since_created} days ago)",
                    inline=False,
                )
                if data.get("last_edit_date") is not None:
                    edited_on = datetime.utcfromtimestamp(data.get("last_edit_date"))
                    edited_since = (ctx.message.created_at - edited_on).days
                    revisions = f"[{edited_since} days ago](https://{subdomain}.stackexchange.com/posts/{data.get('question_id')}/revisions)"
                    em.add_field(
                        name="Question last edited on",
                        value=f"{edited_on.strftime('%d %b, %Y')} ({revisions})",
                        inline=False,
                    )
                recent_activity_on = datetime.utcfromtimestamp(
                    data.get("last_activity_date")
                )
                since_activity = (ctx.message.created_at - recent_activity_on).days
                em.add_field(
                    name="Last activity on",
                    value=f"{recent_activity_on.strftime('%d %b, %Y')} ({since_activity} days ago)",
                    inline=False,
                )
                if data.get("score") > 0:
                    score = f"Question score: {humanize_number(data.get('score'))}"
                if data.get("view_count") > 0:
                    views = f"Views: {humanize_number(data.get('view_count'))}"
                if data.get("answer_count") > 0:
                    answers = f"Answers: {humanize_number(data.get('answer_count'))}"
                em.set_footer(
                    text=f"{score} | {views} | {answers} | Content license: {data.get('content_license', 'None')}"
                )
                embed_list.append(em)

        if not embed_list:
            return await ctx.send("No results.")
        elif len(embed_list) == 1:
            return await ctx.send(embed=embed_list[0])
        else:
            await menu(ctx, embed_list, DEFAULT_CONTROLS, timeout=60.0)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def askubuntu(self, ctx: commands.Context, *, query: str):
        """Search for your query on any of stackexchange domain sites.

        Valid stackexchange network subdomains are:
        `academia`, `ai`, `android`, `anime`, `api`, `apple`, `arduino`, `astronomy`, `biology`, `bitcoin`, `blender`, `boardgames`, `chemistry`, `chess`, `chinese`, `codegolf`, `codereview`, `cooking`, `crypto`, `cs`, `cstheory`, `data`, `datascience`, `dba`, `diy`, `drupal`, `dsp`, `earthscience`, `economics`, `electronics`, `emacs`, `english`, `ethereum`, `expressionengine`, `fitness`, `french`, `gamedev`, `garderning`, `german`, `gis`, `graphicdesign`, `hardwarerecs`, `history`, `japanese`, `law`, `linguistics`, `math`, `mathematica`, `meta`, `money`, `movies`, `music`, `networkengineering`, `outdoor`, `photos`, `physics`, `poker`, `psychology`, `raspberrypi`, `rpg`, `russian`, `salesforce`, `scicomp`, `scifi`, `security`, `sharepoint`, `softwareengineering`, `softwarerecs`, `sound`, `spanish`, `sports`, `sqa`, `tex`, `unix`, `ux`, `video`, `webapps`, `webmasters`, `wordpress`, `worldbuilding`
        """
        api_key = (await ctx.bot.get_shared_api_tokens("stackexchange")).get("api_key")
        api_key = api_key if api_key else ""

        params = {
            "order": "asc",
            "sort": "relevance",
            "q": query,
            "key": api_key,
            "site": "askubuntu",
        }

        async with ctx.typing():
            try:
                async with self.session.get(BASE_API_URL, params=params) as response:
                    if response.status == 200:
                        items = await response.json()
                    else:
                        return await ctx.send(f"https://http.cat/{response.status}")
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            if items.get("quota_remaining") == 0:
                return await ctx.send(
                    "You have exhausted your daily API calls quota. Please try again tomorrow."
                )
            if len(items.get("items")) == 0:
                return await ctx.send("No results")
            embed_list = []
            for data in items.get("items"):
                em = discord.Embed(color=await ctx.embed_colour())
                em.title = unescape(data.get("title", "None"))
                em.url = data.get("link")
                if data.get("accepted_answer_id") is not None:
                    em.description = f"**Accepted answer**: https://askubuntu.com/a/{data.get('accepted_answer_id')}"
                question_owner = (
                    "["
                    + unescape(data.get("owner").get("display_name", "Unknown"))
                    + "]("
                    + data.get("owner").get("link")
                    + ")"
                )
                em.add_field(name="Asked by", value=question_owner)
                em.add_field(name="Tags", value=", ".join(data.get("tags")))
                created_on = datetime.utcfromtimestamp(data.get("creation_date"))
                since_created = (ctx.message.created_at - created_on).days
                em.add_field(
                    name="Question asked on",
                    value=f"{created_on.strftime('%d %b, %Y')} ({since_created} days ago)",
                    inline=False,
                )
                if data.get("last_edit_date") is not None:
                    edited_on = datetime.utcfromtimestamp(data.get("last_edit_date"))
                    edited_since = (ctx.message.created_at - edited_on).days
                    revisions = f"[{edited_since} days ago](https://askubuntu.com/posts/{data.get('question_id')}/revisions)"
                    em.add_field(
                        name="Question last edited on",
                        value=f"{edited_on.strftime('%d %b, %Y')} ({revisions})",
                        inline=False,
                    )
                recent_activity_on = datetime.utcfromtimestamp(
                    data.get("last_activity_date")
                )
                since_activity = (ctx.message.created_at - recent_activity_on).days
                em.add_field(
                    name="Last activity on",
                    value=f"{recent_activity_on.strftime('%d %b, %Y')} ({since_activity} days ago)",
                    inline=False,
                )
                if data.get("score") > 0:
                    score = f"Question score: {humanize_number(data.get('score'))}"
                if data.get("view_count") > 0:
                    views = f"Views: {humanize_number(data.get('view_count'))}"
                if data.get("answer_count") > 0:
                    answers = f"Answers: {humanize_number(data.get('answer_count'))}"
                em.set_footer(
                    text=f"{score} | {views} | {answers} | Content license: {data.get('content_license', 'None')}"
                )
                embed_list.append(em)

        if not embed_list:
            return await ctx.send("No results.")
        elif len(embed_list) == 1:
            return await ctx.send(embed=embed_list[0])
        else:
            await menu(ctx, embed_list, DEFAULT_CONTROLS, timeout=60.0)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def superuser(self, ctx: commands.Context, *, query: str):
        """Search for your query on any of stackexchange domain sites.

        Valid stackexchange network subdomains are:
        `academia`, `ai`, `android`, `anime`, `api`, `apple`, `arduino`, `astronomy`, `biology`, `bitcoin`, `blender`, `boardgames`, `chemistry`, `chess`, `chinese`, `codegolf`, `codereview`, `cooking`, `crypto`, `cs`, `cstheory`, `data`, `datascience`, `dba`, `diy`, `drupal`, `dsp`, `earthscience`, `economics`, `electronics`, `emacs`, `english`, `ethereum`, `expressionengine`, `fitness`, `french`, `gamedev`, `garderning`, `german`, `gis`, `graphicdesign`, `hardwarerecs`, `history`, `japanese`, `law`, `linguistics`, `math`, `mathematica`, `meta`, `money`, `movies`, `music`, `networkengineering`, `outdoor`, `photos`, `physics`, `poker`, `psychology`, `raspberrypi`, `rpg`, `russian`, `salesforce`, `scicomp`, `scifi`, `security`, `sharepoint`, `softwareengineering`, `softwarerecs`, `sound`, `spanish`, `sports`, `sqa`, `tex`, `unix`, `ux`, `video`, `webapps`, `webmasters`, `wordpress`, `worldbuilding`
        """
        api_key = (await ctx.bot.get_shared_api_tokens("stackexchange")).get("api_key")
        api_key = api_key if api_key else ""

        params = {
            "order": "asc",
            "sort": "relevance",
            "q": query,
            "key": api_key,
            "site": "superuser",
        }

        async with ctx.typing():
            try:
                async with self.session.get(BASE_API_URL, params=params) as response:
                    if response.status == 200:
                        items = await response.json()
                    else:
                        return await ctx.send(f"https://http.cat/{response.status}")
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            if items.get("quota_remaining") == 0:
                return await ctx.send(
                    "You have exhausted your daily API calls quota. Please try again tomorrow."
                )
            if len(items.get("items")) == 0:
                return await ctx.send("No results")
            embed_list = []
            for data in items.get("items"):
                em = discord.Embed(color=await ctx.embed_colour())
                em.title = unescape(data.get("title", "None"))
                em.url = data.get("link")
                if data.get("accepted_answer_id") is not None:
                    em.description = f"**Accepted answer**: https://superuser.com/a/{data.get('accepted_answer_id')}"
                question_owner = (
                    "["
                    + unescape(data.get("owner").get("display_name", "Unknown"))
                    + "]("
                    + data.get("owner").get("link")
                    + ")"
                )
                em.add_field(name="Asked by", value=question_owner)
                em.add_field(name="Tags", value=", ".join(data.get("tags")))
                created_on = datetime.utcfromtimestamp(data.get("creation_date"))
                since_created = (ctx.message.created_at - created_on).days
                em.add_field(
                    name="Question asked on",
                    value=f"{created_on.strftime('%d %b, %Y')} ({since_created} days ago)",
                    inline=False,
                )
                if data.get("last_edit_date") is not None:
                    edited_on = datetime.utcfromtimestamp(data.get("last_edit_date"))
                    edited_since = (ctx.message.created_at - edited_on).days
                    revisions = f"[{edited_since} days ago](https://superuser.com/posts/{data.get('question_id')}/revisions)"
                    em.add_field(
                        name="Question last edited on",
                        value=f"{edited_on.strftime('%d %b, %Y')} ({revisions})",
                        inline=False,
                    )
                recent_activity_on = datetime.utcfromtimestamp(
                    data.get("last_activity_date")
                )
                since_activity = (ctx.message.created_at - recent_activity_on).days
                em.add_field(
                    name="Last activity on",
                    value=f"{recent_activity_on.strftime('%d %b, %Y')} ({since_activity} days ago)",
                    inline=False,
                )
                if data.get("score") > 0:
                    score = f"Question score: {humanize_number(data.get('score'))}"
                if data.get("view_count") > 0:
                    views = f"Views: {humanize_number(data.get('view_count'))}"
                if data.get("answer_count") > 0:
                    answers = f"Answers: {humanize_number(data.get('answer_count'))}"
                em.set_footer(
                    text=f"{score} | {views} | {answers} | Content license: {data.get('content_license', 'None')}"
                )
                embed_list.append(em)

        if not embed_list:
            return await ctx.send("No results.")
        elif len(embed_list) == 1:
            return await ctx.send(embed=embed_list[0])
        else:
            await menu(ctx, embed_list, DEFAULT_CONTROLS, timeout=60.0)
