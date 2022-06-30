import asyncio
import contextlib
from typing import Any, Dict, Optional, Union

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number as nfmt

from .stores import AVAILABLE_REGIONS

USER_AGENT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    " (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
}


async def request(url: str, **kwargs) -> Union[int, Dict[str, Any]]:
    params = kwargs.get("params")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=USER_AGENT, params=params) as resp:
                if resp.status != 200:
                    return resp.status
                return await resp.json()
    except (asyncio.TimeoutError, aiohttp.ClientError):
        return 408


class RegionConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        if AVAILABLE_REGIONS.get(argument):
            return AVAILABLE_REGIONS[argument]
        elif argument.upper() in AVAILABLE_REGIONS.values():
            return argument.upper()
        else:
            raise commands.BadArgument(
                "❌ You provided either an invalid country name or"
                " an incorrect 2 letter ISO3166 region code.\n"
                "<https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes>"
            )


class QueryConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, argument: str) -> int:
        # TODO: remove this temp fix once game is released on Steam for all regions
        if argument.lower() == "lost ark":
            return 1599340

        cog = ctx.bot.get_cog("SteamCog")
        user_region = (await cog.config.user(ctx.author).region()) or "US"
        data = await request(
            "https://store.steampowered.com/api/storesearch",
            params={"cc": user_region, "l": "en", "term": argument.lower()}
        )
        if type(data) == int:
            raise commands.BadArgument(f"⚠ API sent response code: https://http.cat/{data}")
        if not data:
            raise commands.BadArgument("❌ No results found from your query.")
        if data.get("total", 0) == 0:
            raise commands.BadArgument("❌ No results found from your query.")
        elif data.get("total") == 1:
            return data.get("items", [{}])[0].get("id")

        def format_price(price_obj: Dict[str, Any], metascore: str) -> str:
            if not price_obj:
                return ""
            currency: str = price_obj.get("currency")
            initial: Optional[int] = price_obj.get("initial")
            final: Optional[int] = price_obj.get("final")
            msg = []
            if initial is not None and final is not None:
                if initial != final:
                    msg.append(f"💵 {currency} ~~{nfmt(initial / 100)}~~ {nfmt(final / 100)}")
                else:
                    msg.append(f"💵 {currency} {nfmt(final / 100)}")
            if metascore:
                msg.append(f"{metascore}% metascore")
            return f" ({', '.join(msg)})" if msg else ""

        # https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
        items = [
            f"**`[{i:>2}]` {app.get('name')}**"
            f"{format_price(app.get('price', {}), app.get('metascore'))}"
            for i, app in enumerate(data.get("items"), start=1)
        ]
        choices = f"Found below **{len(items)}** results. Choose one in 60 seconds:\n\n"
        prompt: discord.Message = await ctx.send(choices + "\n".join(items))

        def check(msg: discord.Message) -> bool:
            return bool(
                msg.content and msg.content.isdigit()
                and int(msg.content) in range(len(items) + 1)
                and msg.author.id == ctx.author.id
                and msg.channel.id == ctx.channel.id
            )

        try:
            choice = await ctx.bot.wait_for("message", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            choice = None
        if choice is None or choice.content.strip() == "0":
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            raise commands.BadArgument("‼ You didn't pick a valid choice. Operation cancelled.")

        with contextlib.suppress(discord.NotFound, discord.HTTPException):
            await prompt.delete()
        return data["items"][int(choice.content.strip()) - 1].get("id")


class GamedealsConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, argument: str) -> int:
        url = f"https://www.cheapshark.com/api/1.0/games?title={argument.lower()}"
        data = await request(url)
        if type(data) == int:
            raise commands.BadArgument(f"⚠ API sent response code: https://http.cat/{data}")
        if not data or len(data) == 0:
            raise commands.BadArgument("❌ No results found.")
        if len(data) == 1:
            return data[0].get("cheapestDealID")

        # https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
        items = "\n".join(
            f"**`[{i:>2}]`** {x.get('external')}" for i, x in enumerate(data[:20], 1)
        )
        count = len(data) if len(data) < 20 else 20
        choices = f"Choose one in 60 seconds:\n\n{items}"
        prompt: discord.Message = await ctx.send(f"Found below **{count}** results. {choices}")

        def check(msg: discord.Message) -> bool:
            return bool(
                msg.content and msg.content.isdigit()
                and int(msg.content) in range(count + 1)
                and msg.author.id == ctx.author.id
                and msg.channel.id == ctx.channel.id
            )

        try:
            choice = await ctx.bot.wait_for("message", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            choice = None

        if choice is None or choice.content.strip() == "0":
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            raise commands.BadArgument("‼ You didn't pick a valid choice. Operation cancelled.")

        with contextlib.suppress(discord.NotFound, discord.HTTPException):
            await prompt.delete()
        return data[int(choice.content.strip()) - 1].get("cheapestDealID")
