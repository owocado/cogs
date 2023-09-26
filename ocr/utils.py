import asyncio
import base64
import logging
from typing import Any

import aiohttp
import dacite
from redbot.core.commands import Context
from redbot.core.utils.chat_formatting import box

from .models import VisionPayload

log = logging.getLogger("red.owo.ocr.utils")


async def _get_bytes(session: aiohttp.ClientSession, url: str):
    if "imgur.com" in url:
        url = f"https://proxy.duckduckgo.com/iu/?u={url}"
    try:
        async with session.get(url) as r:
            buf = await r.read()
    except Exception:
        return None
    else:
        return base64.b64encode(buf).decode('utf-8')


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
        #  out = await free_ocr(ctx.bot.session, image[0])
        #  await ctx.send_interactive(pagify(out))
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
                        "type": "DOCUMENT_TEXT_DETECTION"
                    }
                ],
                "image": {},
                "imageContext": {
                    "textDetectionParams": {
                        "enableTextDetectionConfidenceScore": True
                    }
                }
            }
        ]
    }
    if buf := await _get_bytes(ctx.bot.session, url=image):
        payload["requests"][0]["image"]["content"] = buf
    else:
        payload["requests"][0]["image"]["source"]["imageUri"] = image

    try:
        async with ctx.bot.session.post(base_url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                try:
                    data: dict = await resp.json()
                except Exception:
                    await ctx.send(f"https://http.cat/{resp.status}")
                    return None
                else:
                    p = dacite.from_dict(data_class=VisionPayload, data=data)
                    await ctx.send(str(p.error))
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
        await ctx.send(str(obj.error))
        return None

    return obj

