import asyncio
import functools
import logging
import os

import aiohttp
import discord
import youtube_dl

from moviepy.editor import CompositeVideoClip, TextClip, VideoFileClip

from redbot.core import commands
from redbot.core.data_manager import cog_data_path

logging.captureWarnings(False)


MEME_LINK = "https://youtu.be/U6M7fTbdLbo"

FONT_FILE = "https://github.com/matomo-org/travis-scripts/raw/master/fonts/Verdana.ttf"
log = logging.getLogger("red.owo-cogs.averagefan")


class AverageFan(commands.Cog):
    """
    Create your very own Average Fan Vs Average Enjoyer meme videos.
    """

    __author__ = ["DankMemer Team", "TrustyJAID", "siu3334"]
    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    async def check_video_file(self, link: str, name_template: str) -> bool:
        if not (cog_data_path(self) / name_template).is_file():
            try:
                task = functools.partial(
                    self.dl_from_youtube, link=link, name_template=name_template
                )
                task = self.bot.loop.run_in_executor(None, task)
                await asyncio.wait_for(task, timeout=60)
            except asyncio.TimeoutError:
                log.exception("Error downloading the average meme video")
            except Exception:
                log.error(
                    "Error downloading average meme video template", exc_info=True
                )
                return False
        return True

    def dl_from_youtube(self, link, name_template):
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]",
            "outtmpl": str(cog_data_path(self) / name_template),
        }
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
        except Exception:
            log.exception("Error downloading the video from YouTube.")
            return False
        return True

    async def check_font_file(self) -> bool:
        if not (cog_data_path(self) / "Verdana.ttf").is_file():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(FONT_FILE) as resp:
                        data = await resp.read()
                with open(cog_data_path(self) / "Verdana.ttf", "wb") as save_file:
                    save_file.write(data)
            except Exception:
                log.error("Error downloading Verdana font file", exc_info=True)
                return False
        return True

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.bot_has_permissions(attach_files=True)
    async def averagefan(self, ctx: commands.Context, text1: str, text2: str) -> None:
        """Make Average Fan Vs Average Enjoyer meme videos.

        There must be exactly 1 `,` to split the message
        """
        text1 = text1[:15]
        text2 = text2[:15]
        async with ctx.typing():
            if not await self.check_video_file(MEME_LINK, "meme_template.mp4"):
                return await ctx.send("I couldn't download average fan template video.")
            if not await self.check_font_file():
                return await ctx.send("I couldn't download the font file.")
            fake_task = functools.partial(
                self.make_meme, text1, text2, u_id=ctx.message.id
            )
            task = self.bot.loop.run_in_executor(None, fake_task)

            try:
                await asyncio.wait_for(task, timeout=300)
            except asyncio.TimeoutError:
                # log.error("Error generating memerave video", exc_info=True)
                await ctx.send("Average Meme Video took too long to generate.")
                return
            fp = cog_data_path(self) / f"{ctx.message.id}memerave.mp4"
            file = discord.File(str(fp), filename="memerave.mp4")
            try:
                await ctx.send(files=[file])
            except Exception:
                log.error("Error sending memerave video", exc_info=True)
                pass
            try:
                os.remove(fp)
            except Exception:
                log.error("Error deleting memerave video", exc_info=True)

    def make_meme(self, text1: str, text2: str, u_id: int) -> bool:
        """Non blocking meme rave video generation from DankMemer bot

        https://github.com/DankMemer/meme-server/blob/master/endpoints/meme.py
        """
        fp = str(cog_data_path(self) / f"Verdana.ttf")
        clip = VideoFileClip(str(cog_data_path(self)) + "/meme_template.mp4")
        # clip.volume(0.5)
        text = TextClip(
            text1,
            fontsize=48,
            color="black",
            stroke_width=2,
            stroke_color="black",
            font=fp,
        )
        text = text.set_position((20, 20)).set_duration(15.0)
        text_2 = (
            TextClip(
                text2,
                fontsize=48,
                color="black",
                stroke_width=2,
                stroke_color="black",
                font=fp,
            )
            .set_position((365, 20))
            .set_duration(15.0)
        )

        video = CompositeVideoClip(
            [clip, text.crossfadein(1), text_2.crossfadein(1), text_2.crossfadein(1)]
        ).set_duration(15.0)
        video = video.volumex(1.0)
        video.write_videofile(
            str(cog_data_path(self)) + f"/{u_id}memerave.mp4",
            threads=1,
            preset="superfast",
            verbose=False,
            logger=None,
            temp_audiofile=str(cog_data_path(self) / f"{u_id}memeraveaudio.mp3")
            # ffmpeg_params=["-filter:a", "volume=0.5"]
        )
        clip.close()
        video.close()
        return True
