# This is a slightly modified version of converter originally made by TrustyJAID for his NotSoBot cog
# Attribution at: https://github.com/TrustyJAID/Trusty-cogs/blob/master/notsobot/converter.py
# I have included original LICENSE notice bundled with this cog to adhere to the license terms.
# I am forever indebted to and wholeheartedly thank TrustyJAID for providing this converter.
import re

from typing import Pattern, List, Union

import discord
from discord.ext.commands.converter import Converter
from redbot.core import commands

IMAGE_LINKS: Pattern = re.compile(
    r"(https?:\/\/[^\"\'\s]*\.(?:png|jpg|jpeg|webp|gif)(\?size=[0-9]*)?)", flags=re.I
)


class ImageFinder(Converter):
    """
    This is a class to convert NotSoBot's image searching
    capabilities into a more general converter class
    """

    async def convert(self, ctx: commands.Context, argument: str) -> List[str]:
        attachments = ctx.message.attachments
        matches = IMAGE_LINKS.finditer(argument)
        urls = []
        if matches:
            for match in matches:
                urls.append(match.group(1))
        if attachments:
            for attachment in attachments:
                match = IMAGE_LINKS.match(attachment.url)
                if match:
                    urls.append(match.group(1))
        return urls

    async def find_images_in_replies(self, reference: discord.Message) -> List[str]:
        urls = []
        match = IMAGE_LINKS.search(reference.content)
        if match:
            urls.append(match.group(1))
        if reference.attachments:
            match = IMAGE_LINKS.match(reference.attachments[0].url)
            if match:
                urls.append(match.group(1))
        return urls

    async def search_for_images(self, ctx: commands.Context) -> List[str]:
        urls = []
        async for message in ctx.channel.history(limit=20):
            if message.attachments:
                for attachment in message.attachments:
                    match = IMAGE_LINKS.match(attachment.url)
                    if match:
                        urls.append(match.group(1))
            match = IMAGE_LINKS.search(message.content)
            if match:
                urls.append(match.group(1))
        return urls
