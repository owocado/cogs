from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime
from textwrap import shorten
from typing import List

import discord
from discord.app_commands import Choice
from redbot.core.commands import BadArgument, Context

from .api.base import MediaNotFound
from .api.details import MovieDetails, TVShowDetails
from .api.person import Person as PersonDetails
from .api.search import MovieSearch, PersonSearch, TVShowSearch
from .api.suggestions import MovieSuggestions, TVShowSuggestions
from .utils import format_date


class PersonFinder(discord.app_commands.Transformer):

    async def convert(self, ctx: Context, argument: str):
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
        results = await PersonSearch.request(ctx.cog.session, api_key, argument.lower())
        if isinstance(results, MediaNotFound):
            raise BadArgument(str(results))
        if not results:
            raise BadArgument("⛔ No celebrity or media persons found from given query.")
        if len(results) == 1:
            return await PersonDetails.request(ctx.cog.session, api_key, str(results[0].id))

        items = [
            f"**{i}.**  {obj.name} {obj.famous_for}" for i, obj in enumerate(results, 1)
        ]
        prompt: discord.Message = await ctx.send(
            f"Found below {len(items)} celebrities. Choose one in 60 seconds:\n\n"
            + "\n".join(items)
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

        if choice is None or (choice.content and choice.content.strip() == "0"):
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            raise BadArgument("‼ You didn't pick a valid choice. Operation cancelled.")

        with contextlib.suppress(discord.NotFound, discord.HTTPException):
            await prompt.delete()
        person_id = results[int(choice.content.strip()) - 1].id
        return await PersonDetails.request(ctx.cog.session, api_key, person_id)

    async def transform(self, i: discord.Interaction, value: str):
        key = (await i.client.get_shared_api_tokens('tmdb')).get('api_key', '')
        return await PersonDetails.request(i.client.session, key, value)

    async def autocomplete(
        self, i: discord.Interaction, value: int | float | str
    ) -> List[Choice]:
        token = (await i.client.get_shared_api_tokens('tmdb')).get('api_key', '')
        results = await PersonSearch.request(i.client.session, token, str(value))
        if not results or isinstance(results, MediaNotFound):
            return []

        choices = [
            Choice(name=shorten(f'{p.name} {p.famous_for}', 94), value=str(p.id))
            for p in results
        ]
        return choices[:24]


class MovieFinder(discord.app_commands.Transformer):

    async def convert(self, ctx: Context, argument: str):
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
        results = await MovieSearch.request(ctx.cog.session, api_key, argument.lower())
        if isinstance(results, MediaNotFound):
            raise BadArgument(str(results))
        if not results:
            raise BadArgument("⛔ No such movie found from given query.")
        if len(results) == 1:
            return await MovieDetails.request(ctx.cog.session, api_key, results[0].id)

        # https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
        items = [
            f"**{i}.**  {obj.title} ({format_date(obj.release_date, 'd')})"
            for i, obj in enumerate(results, start=1)
        ]
        prompt: discord.Message = await ctx.send(
            f"Found below {len(items)} movies. Choose one in 60 seconds:\n\n"
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

        if choice is None or (choice.content and choice.content.strip() == "0"):
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            raise BadArgument("‼ You didn't pick a valid choice. Operation cancelled.")

        with contextlib.suppress(discord.NotFound, discord.HTTPException):
            await prompt.delete()
        movie_id = results[int(choice.content.strip()) - 1].id
        return await MovieDetails.request(ctx.cog.session, api_key, movie_id)

    async def transform(self, i: discord.Interaction, value: str):
        key = (await i.client.get_shared_api_tokens('tmdb')).get('api_key', '')
        if i.command and 'suggest' in i.command.name:
            return await MovieSuggestions.request(i.client.session, key, value)
        return await MovieDetails.request(i.client.session, key, value)

    async def autocomplete(
        self, i: discord.Interaction, value: int | float | str
    ) -> List[Choice]:
        token = (await i.client.get_shared_api_tokens('tmdb')).get('api_key', '')
        results = await MovieSearch.request(i.client.session, token, str(value))
        if not results or isinstance(results, MediaNotFound):
            return []

        def parser(title: str, date: str | None) -> str:
            if not date:
                return shorten(title, 94)
            date = datetime.strptime(date, '%Y-%m-%d').strftime('%d %b, %Y')
            return f"{shorten(title, 75, placeholder=' …')} ({date})"

        choices = [
            Choice(
                name=f"{parser(movie.title, movie.release_date)}",
                value=str(movie.id)
            )
            for movie in results
        ]
        return choices[:24]


class TVShowFinder(discord.app_commands.Transformer):

    async def convert(self, ctx: Context, argument: str):
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key", "")
        results = await TVShowSearch.request(ctx.cog.session, api_key, argument.lower())
        if isinstance(results, MediaNotFound):
            raise BadArgument(str(results))
        if not results:
            raise BadArgument("⛔ No such TV show found from given query.")
        if len(results) == 1:
            return await TVShowDetails.request(ctx.cog.session, api_key, results[0].id)

        # https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
        items = [
            f"**{i}.**  {v.name or v.original_name}"
            f" ({format_date(v.first_air_date, 'd', prefix='first aired on ')})"
            for i, v in enumerate(results, start=1)
        ]
        prompt: discord.Message = await ctx.send(
            f"Found below {len(items)} TV shows. Choose one in 60 seconds:\n\n"
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

        if choice is None or (choice.content and choice.content.strip() == "0"):
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            raise BadArgument("‼ You didn't pick a valid choice. Operation cancelled.")

        with contextlib.suppress(discord.NotFound, discord.HTTPException):
            await prompt.delete()
        tv_id = results[int(choice.content.strip()) - 1].id
        return await TVShowDetails.request(ctx.cog.session, api_key, tv_id)

    async def transform(self, i: discord.Interaction, value: str):
        key = (await i.client.get_shared_api_tokens('tmdb')).get('api_key', '')
        if i.command and 'suggest' in i.command.name:
            return await TVShowSuggestions.request(i.client.session, key, value)
        return await TVShowDetails.request(i.client.session, key, value)

    async def autocomplete(
        self, i: discord.Interaction, value: int | float | str
    ) -> List[Choice]:
        if not value:
            return []

        token = (await i.client.get_shared_api_tokens('tmdb')).get('api_key', '')
        results = await TVShowSearch.request(i.client.session, token, str(value))
        if not results or isinstance(results, MediaNotFound):
            return []

        def parser(title: str, date: str | None) -> str:
            if not date:
                return shorten(title, 94)
            date = datetime.strptime(date, '%Y-%m-%d').strftime('%d %b, %Y')
            return f'{shorten(title, 75)} (began on {date})'

        choices = [
            Choice(
                name=f"{parser(tvshow.name, tvshow.first_air_date)}",
                value=str(tvshow.id)
            )
            for tvshow in results
        ]
        return choices[:24]
