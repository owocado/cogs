import asyncio
import docker
import functools
import os
import tempfile
import re
import io

from pathlib import Path
from typing import Optional

import discord
from redbot.core import commands


dockerclient = docker.from_env()


# The code is taken from https://github.com/ManimCommunity/DiscordManimator
# to port it for Red bot. LICENSE is included with the cog to respect authors.
# All credits belong to the Manim Community Developers and not me. Thanks.


class Manim(commands.Cog):
    """A cog for interacting with Manim python animation engine."""

    __author__ = "Manim Community Developers, siu3334"
    __version__ = "0.0.4"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    @commands.bot_has_permissions(attach_files=True)
    async def manimate(self, ctx: commands.Context, *, snippet: str):
        """Evaluate short Manim code snippets to render mathematical animations.
        Code **must** be properly formatted and indented in a markdown code block.

        Supported (CLI) flags:
        ```
        -t, --transparent, -i, --save_as_gif, -s, --save_last_frame
        ```
        Example:
        ```py
        !manimate -s
        def construct(self):
            self.play(ReplacementTransform(Square(), Circle()))
        ```
        """
        async with ctx.typing():
            task = functools.partial(self.construct_reply, arg=snippet)
            task = self.bot.loop.run_in_executor(None, task)
            try:
                reply_args = await asyncio.wait_for(task, timeout=120)
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

        await ctx.reply(**reply_args)

    def construct_reply(self, arg: str) -> Optional[discord.File]:
        if arg.startswith("```"):  # empty header
            arg = "\n" + arg
        header, *body = arg.split("\n")

        cli_flags = header.split()
        allowed_flags = [
            "-i",
            "--save_as_gif",
            "-s",
            "--save_last_frame",
            "-t",
            "--transparent",
        ]
        if not all([flag in allowed_flags for flag in cli_flags]):
            reply_args = {
                "content": "You cannot pass CLI flags other than "
                + "`-i` (`--save_as_gif`), `-s` (`--save_last_frame`), `-t` (`--transparent`)."
            }
            return reply_args
        else:
            cli_flags = " ".join(cli_flags)

        body = "\n".join(body).strip()

        if body.count("```") != 2:
            reply_args = {
                "content": "Your message is not properly formatted. "
                + "Your code has to be written in a code block, like so:\n"
                + "\\`\\`\\`py\nyour code here\n\\`\\`\\`"
            }
            return reply_args

        script = re.search(
            pattern=r"```(?:py)?(?:thon)?(.*)```",
            string=body,
            flags=re.DOTALL,
        ).group(1)
        script = script.strip()

        # for convenience: allow construct-only:
        if script.startswith("def construct(self):"):
            script = "class Manimation(Scene):" + "\n".join(["    " + line for line in script.split("\n")])
        else:
            script = script.split("\n")

        script = ["from manim import *"] + script

        # write code to temporary file (ideally in temporary directory)
        with tempfile.TemporaryDirectory() as tmpdirname:
            scriptfile = Path(tmpdirname) / "script.py"
            with open(scriptfile, "w", encoding="utf-8") as f:
                f.write("\n".join(script))
            try:
                reply_args = None
                container_stderr = dockerclient.containers.run(
                    image="manimcommunity/manim:stable",
                    volumes={tmpdirname: {"bind": "/manim/", "mode": "rw"}},
                    command=f"timeout 120 manim -qm --disable_caching --progress_bar=none -o scriptoutput {cli_flags} /manim/script.py",
                    user=os.getuid(),
                    stderr=True,
                    stdout=False,
                    remove=True,
                )
                if container_stderr:
                    if len(container_stderr.decode("utf-8")) <= 2000:
                        reply_args = {
                            "content": "Something went wrong, here is what Manim reports:\n"
                            + f"```\n{container_stderr.decode('utf-8')}\n```"
                        }
                    else:
                        reply_args = {
                            "content": "Something went wrong, here is the error log:\n",
                            "file": discord.File(
                                fp=io.BytesIO(container_stderr),
                                filename="Error.log",
                            ),
                        }
                    return reply_args
            except Exception as e:
                reply_args = {"content": f"Something went wrong while evaluating provided code snippet:\n```py\n{e}```"}
                return reply_args

            try:
                [outfilepath] = Path(tmpdirname).rglob("scriptoutput.*")
            except Exception as e:
                reply_args = {
                    "content": "Something went wrong: no (unique) output file was produced. :cry:"
                }
                return reply_args

            reply_args = {
                "content": "Here you go:",
                "file": discord.File(outfilepath),
            }
            return reply_args
