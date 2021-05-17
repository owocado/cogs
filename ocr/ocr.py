import aiohttp
import asyncio

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify

from .converter import ImageFinder


class OCR(commands.Cog):
    """Detect text in images using (OCR) Google Cloud Vision API."""

    __author__ = ["TrustyJAID", " siu3334 (<@306810730055729152>)"]
    __version__ = "0.0.3"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def ocr(self, ctx: commands.Context, image: str = None):
        """Run an image through Google Cloud Vision OCR API and return any detected text.

        This command utilizes Google Cloud Vision API.
        Go to this link to enable the Cloud Vision API:
        https://console.cloud.google.com/flows/enableapi?apiid=vision.googleapis.com

        Once you have enabled this API, go to Credentials section to create an API key:
        https://console.cloud.google.com/apis/credentials

        Copy the API key and set it in your red instance with:
        ```
        [p]set api google_vision api_key <copied_api_key>
        ```
        """
        api_key = (await ctx.bot.get_shared_api_tokens("google_vision")).get("api_key")
        if not api_key:
            return await ctx.send_help()

        if image is None:
            image = await ImageFinder().search_for_images(ctx)
            image = image[0]
        if not image:
            return await ctx.send("No images detected.")
        async with ctx.typing():
            base_url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
            headers = {"Content-Type": "application/json;charset=utf-8"}
            payload = {
                "requests": [
                    {
                        "image": {"source": {"imageUri": image}},
                        "features": [{"type": "TEXT_DETECTION"}],
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
