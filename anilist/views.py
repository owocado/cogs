from __future__ import annotations

import contextlib
import random
import re
from contextlib import suppress
from textwrap import shorten
from typing import List, Optional, Pattern

import discord
from redbot.core.commands import Context
from redbot.core.utils.embed import FUNNY_GIFS

CLEAN_RE: Pattern[str] = re.compile(r" • Page \d{1,2} of \d{1,2}")


def get_summary(embed: discord.Embed, use_footer: bool) -> str:
    if use_footer:
        text = (CLEAN_RE.sub("", embed.footer.text or ""))
    elif embed.description:
        text = next(iter(embed.description.splitlines()), "")
    else:
        text = ""
    if not text:
        return text
    return discord.utils.remove_markdown(shorten(text, 96, placeholder="…"))


class WeebSelect(discord.ui.Select):
    view: WeebView

    def __init__(
        self,
        *,
        custom_id: str,
        options: List[discord.SelectOption],
        placeholder: Optional[str] = None,
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, inter: discord.Interaction) -> None:
        option = self.options[int(self.values[0])]
        emb = (
            inter.message or await inter.original_response()
        ).embeds[0]
        same_title = emb.title == option.label
        if option.description == get_summary(emb, self.view.use_footer) and same_title:
            await inter.followup.send(
                "you selected the same entry that's shown in the embed above!\n"
                "Maybe try again and pick a different entry if you like! 👍🏽 🫡",
                ephemeral=True,
            )
            return
        with contextlib.suppress(discord.HTTPException):
            await inter.followup.edit_message(
                self.view.message.id,
                embed=self.view.embeds[int(self.values[0])]
            )
        return


class WeebView(discord.ui.View):

    def __init__(
        self,
        *,
        ctx: Context,
        pages: List[discord.Embed],
        message: discord.Message = discord.utils.MISSING,
        timeout: float = 60,
        use_footer: bool = False,
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.funny = random.choice(FUNNY_GIFS)
        self.message = message
        self.embeds = pages
        self.use_footer = use_footer
        self.add_item(
            WeebSelect(
                custom_id="merlin_anilist_dropdown_view",
                placeholder="Pick a different entry …",
                options=[
                    discord.SelectOption(
                        label=shorten(emb.title or 'N/A', 90, placeholder='…'),
                        value=str(idx),
                        description=get_summary(emb, use_footer),
                    )
                    for idx, emb in enumerate(pages)
                ],
            )
        )

    async def on_timeout(self) -> None:
        self.stop()
        with suppress(discord.NotFound, discord.HTTPException):
            await self.message.edit(view=None)

    async def interaction_check(self, inter: discord.Interaction, /) -> bool:
        if self.ctx.author.id != inter.user.id:
            await inter.response.send_message(self.funny, ephemeral=True)
            return False
        await inter.response.defer()
        return True

