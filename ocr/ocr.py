import asyncio
import json
from typing import Optional

import aiohttp
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, pagify

from .converter import ImageFinder


def is_apikey_set():
    async def predicate(ctx):
        return bool(await ctx.bot.get_shared_api_tokens("google_vision"))
    return commands.check(predicate)


class OCR(commands.Cog):
    """Detect text in images using (OCR) Google Cloud Vision API."""

    __authors__ = "ow0x, TrustyJAID"
    __version__ = "0.1.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {self.__authors__}\nCog Version: {self.__version__}"

    def __init__(self, bot: Red):
        self.bot = bot
        self.sussy_string = "7d3306461d88957"
        self.session = aiohttp.ClientSession()

    def cog_unload(self) -> None:
        asyncio.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(read_message_history=True)
    async def freeocr(self, ctx: commands.Context, *, image: ImageFinder = None):
        """Detect text in an image through OCR.

        This utilises ocr.space API which usually gives poor or subpar results.
        This also assumes the text in image will be in English language.
        """
        await ctx.trigger_typing()
        if image is None:
            if ctx.message.reference:
                message = ctx.message.reference.resolved
                image = await ImageFinder().find_images_in_replies(message)
            else:
                image = await ImageFinder().search_for_images(ctx)
        if not image:
            return await ctx.send("No images or direct image links were detected. 😢")

        file_type = image[0].split(".").pop().upper()
        data = {
            "url": image[0],
            "apikey": self.sussy_string,
            "language": "eng",
            "isOverlayRequired": False,
            "filetype": file_type
        }
        async with self.session.post("https://api.ocr.space/parse/image", data=data) as resp:
            if resp.status != 200:
                return await ctx.send(f"https://http.cat/{resp.status}")
            result = await resp.json()

        if not result.get("ParsedResults"):
            return await ctx.send(box(json.dumps(result), "json"))

        await ctx.send(result["ParsedResults"][0].get("ParsedText"))

    @commands.command()
    @is_apikey_set()
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.bot_has_permissions(read_message_history=True)
    async def ocr(
        self,
        ctx: commands.Context,
        detect_handwriting: Optional[bool] = False,
        *,
        image: ImageFinder = None,
    ):
        """Detect text in an image through OCR.

        This command utilises Google Cloud Vision API.
        """
        api_key = (await ctx.bot.get_shared_api_tokens("google_vision")).get("api_key")

        await ctx.trigger_typing()
        if image is None:
            if ctx.message.reference:
                message = ctx.message.reference.resolved
                image = await ImageFinder().find_images_in_replies(message)
            else:
                image = await ImageFinder().search_for_images(ctx)
        if not image:
            return await ctx.send("No images or direct image links were detected. 😢")

        base_url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
        headers = {"Content-Type": "application/json;charset=utf-8"}
        detect_type = "DOCUMENT_TEXT_DETECTION" if detect_handwriting else "TEXT_DETECTION"
        payload = {
            "requests": [
                {
                    "image": {"source": {"imageUri": image[0]}},
                    "features": [{"type": detect_type}],
                }
            ]
        }

        try:
            async with self.session.post(
                base_url, json=payload, headers=headers
            ) as response:
                if response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                data = await response.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        if data.get("responses")[0] == {}:
            return await ctx.send("No text detected.")
        if (
            data.get("responses")[0].get("error")
            and data.get("responses")[0].get("error").get("message")
        ):
            return await ctx.send(
                f"API returned error: {data['responses'][0]['error']['message']}"
            )
        detected_text = (
            data.get("responses")[0]
            .get("textAnnotations")[0]
            .get("description", "No text detected.")
        )

        await ctx.send_interactive(pagify(detected_text), box_lang="")
