import asyncio
import functools
import os
import tempfile
import textwrap
import traceback
import re
import io
from pathlib import Path
from typing import Any, Dict

import discord
import docker
from redbot.core import commands


# https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/core/dev_commands.py#L31
START_CODE_BLOCK_RE = re.compile(r"((```py(thon)?)(?=\s)|(```))")

dockerclient = docker.from_env()


# The code is taken from https://github.com/ManimCommunity/DiscordManimator
# to port it for Red bot. LICENSE is included with the cog to respect authors.
# All credits belong to the Manim Community Developers and not me. Thanks.


class Manim(commands.Cog):
    """A cog for interacting with Manim python animation engine."""

    __authors__ = ["Manim Community Developers", "owocado"]
    __version__ = "0.17.3"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"Authors:  {', '.join(self.__authors__)}\n"
            f"Cog version:  v{self.__version__}"
        )

    @commands.is_owner()
    @commands.command(aliases=["manimate"])
    @commands.bot_has_permissions(attach_files=True)
    @commands.max_concurrency(1, commands.BucketType.default)
    async def manim(self, ctx: commands.Context, *, snippet: str) -> None:
        """Evaluate short Manim code snippets to render mathematical animations.

        Code **must** be properly formatted and indented in a markdown code block.

        **Supported (CLI) flags:**
            see <https://docs.manim.community/en/stable/guides/configuration.html?highlight=cli%20flags#a-list-of-all-cli-flags>

        **Example:**
        ```py
        [p]manimate -s
        def construct(self):
            self.play(ReplacementTransform(Square(), Circle()))
        ```
        """
        async with ctx.typing():
            fake_task = functools.partial(self.construct_reply, snippet)
            loop = asyncio.get_running_loop()
            task = loop.run_in_executor(None, fake_task)
            try:
                reply_args = await asyncio.wait_for(task, timeout=120)
            except asyncio.TimeoutError:
                await ctx.send("Operation timed out after 2 minutes. No output received from Docker process.")
                return

            reply_args["reference"] = ctx.message.to_reference(fail_if_not_exists=False)
            # reply_args["mention_author"] = False
            await ctx.send(**reply_args)
            return


    def construct_reply(self, script: str) -> Dict[str, Any]:
        if script.count("```") != 2:
            reply_args = {
                "content": "Your message has to be properly formatted "
                " and code should be written in a code block, like so:\n"
                "\\`\\`\\`py\nyour code here\n\\`\\`\\`"
            }
            return reply_args

        arg = START_CODE_BLOCK_RE.sub("", script)
        header, *code = arg.split("\n")

        cli_flags = header.split()
        if "--renderer=opengl" in cli_flags:
            cli_flags.append("--write_to_movie")
        joined_flags = " ".join(cli_flags)

        body = "\n".join(code).strip()

        # for convenience: allow construct-only:
        if body.startswith("def construct(self):"):
            code_snippet = "class Manimation(Scene):\n%s" % textwrap.indent(body, "    ")
        else:
            code_snippet = body

        code_snippet = "from manim import *\n\n" + code_snippet

        # write code to temporary file (ideally in temporary directory)
        base_flags = "-qm --disable_caching --progress_bar=none -o scriptoutput"
        with tempfile.TemporaryDirectory() as tmpdirname:
            with open(Path(tmpdirname) / "script.py", "w", encoding="utf-8") as f:
                f.write(code_snippet)

            reply_args = None
            try:
                dockerclient.containers.run(
                    image="manimcommunity/manim:stable",
                    volumes={tmpdirname: {"bind": "/manim/", "mode": "rw"}},
                    command=f"timeout 120 manim {base_flags} {joined_flags} /manim/script.py",
                    user=os.getuid(),
                    stderr=True,
                    stdout=False,
                    remove=True,
                )
            except Exception as exc:
                if isinstance(exc, docker.errors.ContainerError):
                    tb = exc.stderr
                else:
                    tb = str.encode(traceback.format_exc())
                reply_args = {
                    "content": "Something went wrong, the error log is attached.",
                    "file": discord.File(fp=io.BytesIO(tb), filename="error.log"),
                }
            finally:
                if reply_args:
                    return reply_args

            try:
                [outfilepath] = Path(tmpdirname).rglob("scriptoutput.*")
            except Exception as exc:
                tb = str.encode(traceback.format_exc())
                reply_args = {
                    "content": "Something went wrong; the error.log is attached.",
                    "file": discord.File(fp=io.BytesIO(tb), filename="error.log"),
                }
                return reply_args
            else:
                reply_args = {
                    "content": "Here you go:",
                    "file": discord.File(outfilepath),
                }
            finally:
                return reply_args
