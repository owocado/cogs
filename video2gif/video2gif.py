import asyncio
import functools
import logging
import os

from typing import Any, Dict, Literal

import aiohttp
import discord
import youtube_dl
from moviepy.editor import VideoFileClip
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
from redbot.core.utils.predicates import MessagePredicate

log = logging.getLogger("red.owo-cogs.video2gif")

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class VideoToGIF(commands.Cog):
    """Converts given MP4 video attachment to GIF file format."""

    __author__ = ["TrustyJAID", "ow0x"]
    __version__ = "0.1.1"

    def __init__(self, bot):
        self.bot = bot

    # credits to jack1142
    async def red_get_data_for_user(self, *, user_id: int) -> Dict[str, Any]:
        # this cog does not story any data
        return {}

    async def red_delete_data_for_user(
        self, *, requester: RequestType, user_id: int
    ) -> None:
        # this cog does not story any data
        pass

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """
        Thanks Sinbad!
        """
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    @commands.command()
    @commands.is_owner()
    @commands.cooldown(1, 120, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(attach_files=True)
    async def video2gif(self, ctx: commands.Context):
        """Converts given video attachment to GIF."""

        # Credits to https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/cogs/trivia/trivia.py#L246
        if not ctx.message.attachments:
            await ctx.send("Supply a file with next message or type anything to cancel.")
            try:
                message = await ctx.bot.wait_for(
                    "message", check=MessagePredicate.same_context(ctx), timeout=30
                )
            except asyncio.TimeoutError:
                await ctx.send("You took too long to upload a file.")
                return
            if not message.attachments:
                await ctx.send("You have cancelled the upload process.")
                return
            parsedfile = message.attachments[0].url
            if not parsedfile.endswith("mp4"):
                return await ctx.send("Only attachment with .MP4 extension is supported.")
        else:
            parsedfile = ctx.message.attachments[0].url
            if not parsedfile.endswith("mp4"):
                return await ctx.send("Only attachment with .MP4 extension is supported.")
        # Below entire code snippet till end taken from
        # https://github.com/TrustyJAID/Trusty-cogs/blob/master/crabrave/crabrave.py#L98
        # Thank you Trusty senpai <3
        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(parsedfile) as response:
                        data = await response.read()
                with open(cog_data_path(self) / "video0.mp4", "wb") as save_file:
                    save_file.write(data)
            except Exception:
                log.error("Error downloading video from message attachment.", exc_info=True)
            fake_task = functools.partial(self.make_gif, u_id=ctx.message.id)
            task = self.bot.loop.run_in_executor(None, fake_task)

            try:
                await asyncio.wait_for(task, timeout=300)
            except asyncio.TimeoutError:
                # log.error("Error generating GIF from video.", exc_info=True)
                await ctx.send("It took too long to convert the video to GIF. :(")
                return
            fp = cog_data_path(self) / f"{ctx.message.id}_final.gif"
            mp4 = cog_data_path(self) / f"video0.mp4"
            file = discord.File(str(fp), filename="final.gif")
            try:
                await ctx.send(files=[file])
            except (discord.errors.HTTPException, FileNotFoundError):
                await ctx.send("Failed to upload GIF. Request entity too large.")
                log.error("Error sending converted GIF to destination channel.", exc_info=True)
                pass
            try:
                os.remove(fp)
                os.remove(mp4)
            except Exception:
                log.error("Error deleting processed GIFs and original attachment.", exc_info=True)

    def make_gif(self, u_id: int) -> bool:
        """video to GIF conversion"""
        clip = VideoFileClip(str(cog_data_path(self)) + "/video0.mp4", audio=False)
        clip = clip.resize(0.5)
        clip.write_videofile(str(cog_data_path(self)) + f"/{u_id}_final.gif", fps=10, codec='gif', audio=False, preset='slower', threads=2, logger=None)
        clip.close()
        return True
