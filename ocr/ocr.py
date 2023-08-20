import asyncio
import logging
from typing import Optional

import aiohttp
from redbot.core import commands, __version__ as red_version
from redbot.core.utils.chat_formatting import box, pagify

from .converter import ImageFinder

log = logging.getLogger("red.owo-cogs.ocr")


class OCR(commands.Cog):
    """Detect text in images using ocr.space or Google Cloud Vision API."""

    __authors__ = ["TrustyJAID", "<@306810730055729152>"]
    __version__ = "1.2.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(self.__authors__)}\n"
            f"**Cog version:**  v{self.__version__}"
        )

    sussy_string = "7d3306461d88957"
    session = aiohttp.ClientSession()

    def cog_unload(self) -> None:
        if self.session:
            asyncio.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    async def _free_ocr(self, ctx: commands.Context, image: str):
        file_type = image.split(".").pop().upper()
        data = {
            "url": image,
            "apikey": self.sussy_string,
            "language": "eng",
            "isOverlayRequired": False,
            "filetype": file_type
        }

        async def query_kaogurai(url: str) -> dict[str, Any] | None:
            headers = {
                "Accept": "application/json",
                "User-Agent": f"Red-DiscordBot, OCR/2.0.0 (https://github.com/kaogurai/cogs)"
            }
            prms = {"url": image_url}
            async with session.get(url, headers=headers, params=prms) as resp:
                if resp.status != 200:
                    log.info(f"[OCR] {url} sent {resp.status} HTTP response code.")
                    return None
                return await resp.json()

        result = await query_kaogurai("https://api.flowery.pw/v1/ocr")
        if not result:
            async with self.session.post(
                "https://api.ocr.space/parse/image", data=data
            ) as resp:
                if resp.status != 200:
                    return await ctx.send(f"https://http.cat/{resp.status}")
                result = await resp.json()

        temp_ = result.get("textAnnotations", [{}])
        if (err := temp_[0].get("error")) and (err_message := err.get("message")):
            return await ctx.send(f"API returned error: {err_message}")

        if temp_[0].get("description"):
            return await ctx.send_interactive(
                pagify(temp_[0]["description"]), box_lang=""
            )

        if not result.get("ParsedResults"):
            return await ctx.send(box(str(result.get("ErrorMessage")), "json"))

        return await ctx.send_interactive(
            pagify(result["ParsedResults"][0].get("ParsedText")),
            box_lang="py"
        )

    @commands.command(aliases=["freeocr"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(read_message_history=True)
    async def ocr(
        self,
        ctx: commands.Context,
        detect_handwriting: Optional[bool] = False,
        *,
        image: ImageFinder = None,
    ):
        """Detect text in an image through Google OCR API.

        You may use it to run OCR on old messages which contains attachments/image links.
        Simply reply to the said message with `[p]ocr` for detection to work.

        Pass `detect_handwriting` as True or `1` with command to more accurately detect handwriting from target image.

        **Example:**
        ```py
        [p]ocr image/attachment/URL
        # To better detect handwriting in target image
        [p]ocr 1 image/attachment/URL
        ```
        """
        api_key = (await ctx.bot.get_shared_api_tokens("google_vision")).get("api_key")

        async with ctx.typing():
            if image is None:
                if ctx.message.reference:
                    message = ctx.message.reference.resolved
                    image = await ImageFinder().find_images_in_replies(message)
                else:
                    image = await ImageFinder().search_for_images(ctx)
            if not image:
                return await ctx.send("No images or direct image links were detected. 😢")

            if not api_key:
                return await self._free_ocr(ctx, image[0])

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
                async with self.session.post(base_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    data = await response.json()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

        output = data.get("responses")
        if not output or output[0] == {}:
            return await ctx.send("No text detected.")
        if (err := output[0].get("error")) and (err_message := err.get("message")):
            return await ctx.send(f"API returned error: {err_message}")

        detected_text = output[0].get("textAnnotations", [{}])[0].get("description")
        if not detected_text:
            return await ctx.send("No text was detected in the target image.")

        await ctx.send_interactive(pagify(detected_text), box_lang="")
