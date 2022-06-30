import asyncio
import urllib.parse
from contextlib import suppress
from typing import cast

import aiohttp
import discord
from bs4 import BeautifulSoup as bsp, element
from redbot.core import commands

try:
    import lxml  # type: ignore
    PARSER = "lxml"
except ImportError:
    PARSER = "html.parser"

BASE_URL = "https://www.gsmarena.com/results.php3?sQuickSearch=yes&sName={}"

USER_AGENT = {
    "Accept": "text/html,application/xhtml+xml,application/xml",
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    " (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
}


class QueryConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    BASE_URL.format(urllib.parse.quote_plus(argument)), headers=USER_AGENT
                ) as resp:
                    if resp.status != 200:
                        raise commands.BadArgument(
                            f"⚠ GSMarena returned status code {resp.status}."
                        )
                    data = await resp.text()
        except (asyncio.TimeoutError, aiohttp.ClientError):
            raise commands.BadArgument("⚠ Operation timed out!")

        soup = bsp(data, features=PARSER).find("div", {"class": "makers"})
        get_ul_div = cast(element.Tag, soup.find("ul"))
        makers = get_ul_div.find_all("li")
        if not makers:
            raise commands.BadArgument("⚠ No results found.")

        if len(makers) == 1:
            return makers[0].a["href"]

        items = [
            f"**`[{i}]`** {x.span.get_text(separator=' ')}" for i, x in enumerate(makers, 1)
        ]

        choices = f"Found above {len(makers)} result(s). Choose one in 60 seconds!"
        embed = discord.Embed(description="\n".join(items)).set_footer(text=choices)
        prompt: discord.Message = await ctx.send(embed=embed)

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
            with suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            raise commands.BadArgument("‼ You didn't pick a valid choice. Operation cancelled.")

        with suppress(discord.NotFound, discord.HTTPException):
            await prompt.delete()
        return makers[int(choice.content.strip()) - 1].a["href"]