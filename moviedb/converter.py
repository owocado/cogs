import asyncio
import contextlib

import discord
from redbot.core.commands import BadArgument, Context, Converter

from .api import MovieSearchData, TVShowSearchData
from .constants import MediaNotFound
from .utils import format_date


class MovieFinder(Converter):

    async def convert(self, ctx: Context, argument: str) -> int:
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
        result = await MovieSearchData.request(api_key, argument.lower())
        if isinstance(result, MediaNotFound):
            raise BadArgument(str(result))
        if not result:
            raise BadArgument("⛔ No such movie found from given query.")

        if len(result) == 1:
            return result[0].id

        # https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
        items = [
            f"**{i}.**  {obj.title} ({format_date(obj.release_date, 'd')})"
            for i, obj in enumerate(result, start=1)
        ]
        prompt: discord.Message = await ctx.send(
            f"Found below {len(items)} results (sorted by date). Choose one in 60 seconds:\n\n"
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
            choice: discord.Message = await ctx.bot.wait_for("message", timeout=60, check=check)
        except asyncio.TimeoutError:
            choice = None

        if choice is None or (choice.content and choice.content.strip() == "0"):
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            raise BadArgument("‼ You didn't pick a valid choice. Operation cancelled.")

        with contextlib.suppress(discord.NotFound, discord.HTTPException):
            await prompt.delete()
        return result[int(choice.content.strip()) - 1].id


class TVShowFinder(Converter):

    async def convert(self, ctx: Context, argument: str) -> int:
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
        result = await TVShowSearchData.request(api_key, argument.lower())
        if isinstance(result, MediaNotFound):
            raise BadArgument(str(result))
        if not result:
            raise BadArgument("⛔ No such TV show found from given query.")

        if len(result) == 1:
            return result[0].id

        # https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
        items = [
            f"**{i}.**  {v.name or v.original_name}"
            f" ({format_date(v.first_air_date, 'd', prefix='first aired on ')})"
            for i, v in enumerate(result, start=1)
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
            choice: discord.Message = await ctx.bot.wait_for("message", timeout=60, check=check)
        except asyncio.TimeoutError:
            choice = None

        if choice is None or (choice.content and choice.content.strip() == "0"):
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            raise BadArgument("‼ You didn't pick a valid choice. Operation cancelled.")

        with contextlib.suppress(discord.NotFound, discord.HTTPException):
            await prompt.delete()
        return result[int(choice.content.strip()) - 1].id
