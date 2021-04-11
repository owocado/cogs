import asyncio
import docker
import os
import tempfile
import re
import io

from pathlib import Path

import discord
from redbot.core import commands


dockerclient = docker.from_env()


# The code is taken from https://github.com/ManimCommunity/DiscordManimator
# to port it for Red bot. LICENSE is included with the cog to respect authors.
# All credits belong to the Manim Community Developers and not me. Thanks.

class Manim(commands.Cog):
    """A cog for interacting with Manim python animation engine."""

    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command(aliases=["manim"])
    @commands.bot_has_permissions(attach_files=True)
    async def manimate(self, ctx: commands.Context, *, arg: str):
        """Render short and simple Manim scripts.
        Code **must** be properly formatted and indented. Note that you can't animate through DM's.

        Supported tags:
        ```
            -t, --transparent, -i, --save_as_gif, -s, --save_last_frame
        ```
        Example:
        ```
        !manimate -s
        def construct(self):
            self.play(ReplacementTransform(Square(), Circle()))
        ```
        """

        def construct_reply(arg):
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
                    "`-i` (`--save_as_gif`), `-s` (`--save_last_frame`), "
                    "`-t` (`--transparent`)."
                }
                return reply_args
            else:
                cli_flags = " ".join(cli_flags)

            body = "\n".join(body).strip()

            if body.count("```") != 2:
                reply_args = {
                    "content": "Your message is not properly formatted. "
                    "Your code has to be written in a code block, like so:\n"
                    "\\`\\`\\`py\nyour code here\n\\`\\`\\`"
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
                script = ["class Manimation(Scene):"] + [
                    "    " + line for line in script.split("\n")
                ]
            else:
                script = script.split("\n")

            script = ["from manim import *"] + script

            # write code to temporary file (ideally in temporary directory)
            with tempfile.TemporaryDirectory() as tmpdirname:
                scriptfile = Path(tmpdirname) / "script.py"
                with open(scriptfile, "w", encoding="utf-8") as f:
                    f.write("\n".join(script))
                try:  # now it's getting serious: get docker involved
                    reply_args = None
                    container_stderr = dockerclient.containers.run(
                        image="manimcommunity/manim:stable",
                        volumes={tmpdirname: {"bind": "/manim/", "mode": "rw"}},
                        command=f"timeout 120 manim /manim/script.py -qm --disable_caching --progress_bar False -o scriptoutput {cli_flags}",
                        user=os.getuid(),
                        stderr=True,
                        stdout=False,
                        remove=True,
                    )
                    if container_stderr:
                        if len(container_stderr.decode("utf-8")) <= 1200:
                            reply_args = {
                                "content": "Something went wrong, here is "
                                "what Manim reports:\n"
                                f"```\n{container_stderr.decode('utf-8')}\n```"
                            }
                        else:
                            reply_args = {
                                "content": "Something went wrong, here is "
                                "what Manim reports:\n",
                                "file": discord.File(
                                    fp=io.BytesIO(container_stderr),
                                    filename="Error.log",
                                ),
                            }

                        return reply_args

                except Exception as e:
                    reply_args = {"content": f"Something went wrong: ```{e}```"}
                    raise e
                finally:
                    if reply_args:
                        return reply_args

                try:
                    [outfilepath] = Path(tmpdirname).rglob("scriptoutput.*")
                except Exception as e:
                    reply_args = {
                        "content": "Something went wrong: no (unique) output file was produced. :cry:"
                    }
                    raise e
                else:
                    reply_args = {
                        "content": "Here you go:",
                        "file": discord.File(outfilepath),
                    }
                finally:
                    return reply_args

        async with ctx.typing():
            reply_args = construct_reply(arg)
            await ctx.reply(**reply_args)
