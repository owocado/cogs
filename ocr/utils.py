import asyncio
import logging
from typing import Any

import aiohttp
import dacite
from redbot.core import __version__ as red_version
from redbot.core.commands import Context
from redbot.core.utils.chat_formatting import box, pagify

from .models import VisionPayload

log = logging.getLogger("red.owo.ocr.utils")



async def free_ocr(session: aiohttp.ClientSession, image_url: str) -> str:
    sussy_string = "7d3306461d88957"
    file_type = image_url.split(".").pop().upper()
    data = {
        "url": image_url,
        "apikey": sussy_string,
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
                log.debug(f"[OCR] {url} sent {resp.status} HTTP response code.")
                return None
            return await resp.json()

    result = await query_kaogurai("https://api.flowery.pw/v1/ocr")
    if not result:
        async with session.post("https://api.ocr.space/parse/image", data=data) as resp:
            if resp.status != 200:
                return f"https://http.cat/{resp.status}.jpg"
            result = await resp.json()

    temp_ = result.get("textAnnotations", [{}])
    if (err := temp_[0].get("error")) and (err_message := err.get("message")):
        return f"API returned error: {err_message}"

    if temp_[0].get("description"):
        return temp_[0]["description"]

    if not result.get("ParsedResults"):
        return box(str(result.get("ErrorMessage")), "json")

    return result["ParsedResults"][0].get("ParsedText")


async def vision_ocr(
    ctx: Context, detect_handwriting: bool | None, image: str
) -> VisionPayload | None:
    api_key = (await ctx.bot.get_shared_api_tokens("google_vision")).get("api_key")
    if not api_key:
        out = await free_ocr(ctx.bot.session, image[0])
        await ctx.send_interactive(pagify(out))
        return None

    base_url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    headers = {"Content-Type": "application/json;charset=utf-8"}
    detect_type = "DOCUMENT_TEXT_DETECTION" if detect_handwriting else "TEXT_DETECTION"
    payload = {
        "requests": [
            {
                "features": [
                    {
                        "model": "builtin/weekly",
                        "type": detect_type
                    }
                ],
                "image": {
                    "source": {
                        "imageUri": image
                    }
                },
                "imageContext": {
                    "textDetectionParams": {
                        "enableTextDetectionConfidenceScore": True
                    }
                }
            }
        ]
    }

    try:
        async with ctx.bot.session.post(base_url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                await ctx.send(f"https://http.cat/{resp.status}")
                return None
            data: dict = await resp.json()
    except (asyncio.TimeoutError, aiohttp.ClientError):
        await ctx.send("Operation timed out.")
        return None

    output: list[dict[str, Any]] = data.get("responses", [])
    if not output or not output[0]:
        await ctx.send("No text detected.")
        return None
    obj = dacite.from_dict(data_class=VisionPayload, data=data['responses'][0])
    if obj.error and obj.error.message:
        await ctx.send(f"Error: {obj.error.message}")
        return None

    return obj
