import asyncio
import contextlib
from datetime import datetime

import aiohttp
import discord
from redbot.core import commands

def parse_date(date_string: str, style: str = "R", *, prefix: str = "") -> str:
    if not date_string:
        return ""
    # TODO: Switch to dateparser if date string changes from API response
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        return f"{prefix}<t:{int(date_obj.timestamp())}:{style}>"
    # Future proof it in case API changes date string
    except ValueError:
        return ""


async def request(url: str, *, params: dict = None) -> aiohttp.ClientResponse:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return resp.status
                return await resp.json()
    except (asyncio.TimeoutError, aiohttp.ClientError):
        return 408


class MovieQueryConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, argument: str) -> int:
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        data = await request(
            "https://api.themoviedb.org/3/search/movie",
            params={"api_key": api_key, "query": argument.lower()}
        )
        if type(data) == int:
            raise commands.BadArgument(f"⚠ API sent response code: https://http.cat/{data}")
        if not data:
            raise commands.BadArgument("⛔ No such movie found from given query.")

        if not data.get("results") or len(data.get("results")) == 0:
            raise commands.BadArgument("⛔ No such movie found from given query.")
        if len(data.get("results")) == 1:
            return data["results"][0].get("id")

        # https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
        data["results"].sort(key=lambda x: x.get("release_date"), reverse=True)
        items = [
            f"**`[{i:>2}]`** ({parse_date(obj.get('release_date'), 'd')})"
            f"  {obj.get('original_title', '[MOVIE TITLE MISSING]')}"
            for i, obj in enumerate(data["results"], start=1)
        ]
        prompt: discord.Message = await ctx.send(
            f"Found below {len(items)} results. Choose one in 60 seconds:\n\n"
            + "\n".join(items).replace(" ()", "")
        )

        def check(msg: discord.Message) -> bool:
            return bool(
                msg.content and msg.content.isdigit()
                and int(msg.content) in range(len(items) + 1)
                and msg.author.id == ctx.author.id
                and msg.channel.id == ctx.channel.id
            )

        try:
            choice = await ctx.bot.wait_for("message", timeout=60, check=check)
        except asyncio.TimeoutError:
            choice = None

        if choice is None or choice.content.strip() == "0":
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            raise commands.BadArgument("‼ You didn't pick a valid choice. Operation cancelled.")

        with contextlib.suppress(discord.NotFound, discord.HTTPException):
            await prompt.delete()
        return data["results"][int(choice.content.strip()) - 1].get("id")


class TVShowQueryConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, argument: str) -> int:
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        data = await request(
            "https://api.themoviedb.org/3/search/tv",
            params={"api_key": api_key, "query": argument.lower()}
        )
        if type(data) == int:
            raise commands.BadArgument(f"⚠ API sent response code: https://http.cat/{data}")
        if not data:
            raise commands.BadArgument("⛔ No such TV show found from given query.")

        if not data.get("results") or len(data.get("results")) == 0:
            raise commands.BadArgument("⛔ No such TV show found from given query.")
        if len(data.get("results")) == 1:
            return data["results"][0].get("id")

        # https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
        data["results"].sort(key=lambda x: x.get("first_air_date"), reverse=True)
        items = [
            f"**`[{i:>2}]`  {v.get('original_name', '[TVSHOW TITLE MISSING]')}**"
            f" ({parse_date(v.get('first_air_date'), 'd', prefix='first aired on ')})"
            for i, v in enumerate(data["results"], start=1)
        ]
        prompt: discord.Message = await ctx.send(
            f"Found below {len(items)} results. Choose one in 60 seconds:\n\n"
            + "\n".join(items).replace(" ()", "")
        )

        def check(msg: discord.Message) -> bool:
            return bool(
                msg.content and msg.content.isdigit()
                and int(msg.content) in range(len(items) + 1)
                and msg.author.id == ctx.author.id
                and msg.channel.id == ctx.channel.id
            )

        try:
            choice = await ctx.bot.wait_for("message", timeout=60, check=check)
        except asyncio.TimeoutError:
            choice = None

        if choice is None or choice.content.strip() == "0":
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            raise commands.BadArgument("‼ You didn't pick a valid choice. Operation cancelled.")

        with contextlib.suppress(discord.NotFound, discord.HTTPException):
            await prompt.delete()
        return data.get("results")[int(choice.content.strip()) - 1].get("id")
