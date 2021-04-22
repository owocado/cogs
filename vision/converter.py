# This is a slightly modified version of converter originally made by TrustyJAID for his NotSoBot cog
# Attribution at: https://github.com/TrustyJAID/Trusty-cogs/blob/master/notsobot/converter.py
# I have included original LICENSE notice bundled with this cog to adhere to the license terms.
# I am forever indebted to and wholeheartedly thank TrustyJAID for providing this converter.
import re

from typing import Pattern, List, Union

import discord
from discord.ext.commands.converter import Converter
from discord.ext.commands.errors import BadArgument
from redbot.core import commands

IMAGE_LINKS: Pattern = re.compile(
    r"(https?:\/\/[^\"\'\s]*\.(?:png|jpg|jpeg|png|svg)(\?size=[0-9]*)?)", flags=re.I
)


class ImageFinder(Converter):
    """
    This is a class to convert NotSoBot's image searching
    capabilities into a more general converter class
    """

    async def convert(
        self, ctx: commands.Context, argument: str
    ) -> List[Union[discord.Asset, str]]:
        attachments = ctx.message.attachments
        matches = IMAGE_LINKS.finditer(argument)
        urls = []
        if matches:
            for match in matches:
                urls.append(match.group(1))
        if attachments:
            for attachment in attachments:
                urls.append(attachment.url)
        if not urls:
            raise BadArgument("No images provided.")
        return urls[0]

    async def search_for_images(
        self, ctx: commands.Context
    ) -> List[Union[discord.Asset, discord.Attachment, str]]:
        urls = []
        if not ctx.channel.permissions_for(ctx.me).read_message_history:
            raise BadArgument("I require read message history perms to find images.")
        async for message in ctx.channel.history(limit=20):
            if message.attachments:
                for attachment in message.attachments:
                    urls.append(attachment.url)
            match = IMAGE_LINKS.match(message.content)
            if match:
                urls.append(match.group(1))
        if not urls:
            raise BadArgument("No Images found in recent history.")
        return urls[0]
