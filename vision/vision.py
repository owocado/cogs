import aiohttp
import asyncio
import json
import re

from typing import Pattern

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify

# Credits to TrustyJAID (https://github.com/TrustyJAID/Trusty-cogs/blob/master/notsobot/converter.py#L10)
IMAGE_LINKS: Pattern = re.compile(
    r"(https?:\/\/[^\"\'\s]*\.(?:png|jpg|jpeg|webp|svg)(\?size=[0-9]*)?)", flags=re.I
)

# Attribution: taken from https://github.com/flaree/Flare-Cogs/blob/master/dankmemer/dankmemer.py#L16
# Many thanks to flare ❤️
async def tokencheck(ctx):
    token = await ctx.bot.get_shared_api_tokens("google_vision")
    return bool(token.get("api_key"))


class Vision(commands.Cog):
    """Detect text in images using (OCR) Google Cloud Vision API."""

    __author__ = ["<@306810730055729152>"]
    __version__ = "0.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command()
    @commands.check(tokencheck)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def ocr(self, ctx: commands.Context, url: str):
        """Run an image through Google Cloud Vision OCR API and return any detected text."""

        if ctx.message.attachments:
            url = ctx.message.attachments[0].url
        match = IMAGE_LINKS.match(url)
        if match:
            url = match.group(1)
        else:
            return await ctx.send("That doesn't look like a valid direct image URL.")

        api_key = (await ctx.bot.get_shared_api_tokens("google_vision")).get("api_key")
        params = {"key": api_key}
        headers = {"Content-Type": "application/json;charset=utf-8"}
        payload = {
            "requests": [
                {
                    "image": {"source": {"imageUri": url}},
                    "features": [{"type": "TEXT_DETECTION"}],
                }
            ]
        }

        try:
            async with self.session.post(
                "https://vision.googleapis.com/v1/images:annotate",
                params=params,
                json=payload,
                headers=headers,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                else:
                    return await ctx.send(f"https://http.cat/{response.status}")
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        if data.get("responses")[0] == {}:
            return await ctx.send("No text detected.")
        if data.get("responses")[0].get("error").get("message"):
            return await ctx.send(
                f"API returned error: {data.get('responses')[0].get('error').get('message')}"
            )
        detected_text = data.get("responses")[0].get("textAnnotations")[0].get("description", "No text detected.")

        await ctx.send_interactive(pagify(detected_text))
