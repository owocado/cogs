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
    r"(https?:\/\/[^\"\'\s]*\.(?:png|jpg|jpeg|webp|gif)(\?size=[0-9]*)?)", flags=re.I
)


class ImageFinder(Converter):
    """
    This is a class to convert NotSoBot's image searching
    capabilities into a more general converter class
    """

    async def search_for_images(
        self, ctx: commands.Context
    ) -> List[Union[discord.Asset, discord.Attachment, str]]:
        urls = []
        if not ctx.channel.permissions_for(ctx.me).read_message_history:
            raise BadArgument("I require \"Read Message History\" permission to find images in this channel's history.")
        async for message in ctx.channel.history(limit=20):
            if message.attachments:
                for attachment in message.attachments:
                    urls.append(attachment.url)
            match = IMAGE_LINKS.search(message.content)
            if match:
                urls.append(match.group(1))
        if not urls:
            raise BadArgument("No images were found in last 20 messages in this channel.")
        return urls
