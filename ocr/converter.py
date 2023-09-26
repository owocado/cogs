# originally made by TrustyJAID for his NotSoBot cog
# https://github.com/TrustyJAID/Trusty-cogs/blob/master/notsobot/converter.py
import re

from discord import DeletedReferencedMessage, Message
from redbot.core.commands import BadArgument, Context, Converter

IMAGE_LINKS: re.Pattern = re.compile(
    r"(https?:\/\/[^\"\'\s]*\.(?:png|jpg|jpeg|webp)(\?size=[0-9]{1,4})?)",
    flags=re.I
)


class ImageFinder(Converter):
    """
    This is a class to convert NotSoBot's image searching
    capabilities into a more general converter class
    """

    async def convert(self, ctx: Context, argument: str) -> list[str]:
        urls: list[str] = []
        if matches := IMAGE_LINKS.finditer(argument):
            urls.extend(match.group(1) for match in matches)
        if attachments := ctx.message.attachments:
            urls.extend(
                match.group(1)
                for attachment in attachments
                if (match := IMAGE_LINKS.match(attachment.url))
            )
        if not urls:
            if ctx.message.reference and (message := ctx.message.reference.resolved):
                urls = await find_images_in_replies(message)
            else:
                urls = await search_for_images(ctx)
        if not urls:
            raise BadArgument("No images or image links found in chat bro 🥸")
        return urls


async def find_images_in_replies(
    reference: DeletedReferencedMessage | Message | None
) -> list[str]:
    if not reference or not isinstance(reference, Message):
        return []
    urls = []
    if match := IMAGE_LINKS.search(reference.content):
        urls.append(match.group(1))
    if reference.attachments:
        if match := IMAGE_LINKS.match(reference.attachments[0].url):
            urls.append(match.group(1))
    if reference.embeds and reference.embeds[0].image:
        urls.append(reference.embeds[0].image.url)
    return urls


async def search_for_images(ctx: Context) -> list[str]:
    urls = []
    async for message in ctx.channel.history(limit=20):
        if message.embeds and message.embeds[0].image:
            urls.append(message.embeds[0].image.url)
        if message.attachments:
            urls.extend(
                match.group(1)
                for attachment in message.attachments
                if (match := IMAGE_LINKS.match(attachment.url))
            )
        if match := IMAGE_LINKS.search(message.content):
            urls.append(match.group(1))
    return urls

