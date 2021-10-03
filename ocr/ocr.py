import aiohttp
import asyncio
from typing import Optional

from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify

from .converter import ImageFinder


class OCR(commands.Cog):
    """Detect text in images using (OCR) Google Cloud Vision API."""

    __author__ = ["TrustyJAID", "ow0x"]
    __version__ = "0.0.7"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        authors = f"Authors: {', '.join(self.__author__)}"
        return f"{pre_processed}\n\n{authors}\nCog Version: {self.__version__}"

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.bot_has_permissions(read_message_history=True)
    async def ocr(
        self,
        ctx: commands.Context,
        detect_handwriting: Optional[bool] = False,
        *,
        image: ImageFinder = None, 
    ):
        """Run an image through OCR and return any detected text."""
        api_key = (await ctx.bot.get_shared_api_tokens("google_vision")).get("api_key")
        if not api_key:
            return await ctx.send("API key not found. Please set it first.")

        await ctx.trigger_typing()
        detect_type = "DOCUMENT_TEXT_DETECTION" if detect_handwriting else "TEXT_DETECTION"
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
        payload = {
            "requests": [
                {
                    "image": {"source": {"imageUri": image[0]}},
                    "features": [{"type": detect_type}],
                }
            ]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
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
