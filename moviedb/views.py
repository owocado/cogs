from __future__ import annotations

from contextlib import suppress

from discord import Interaction, Message, SelectOption, ui
from discord.utils import MISSING
from redbot.core.commands import Context
from redbot.core.bot import Red


class OfferSelect(ui.Select):
    view: ChoiceView

    def __init__(self, *, options: list[SelectOption]) -> None:
        super().__init__(options=options, placeholder="Pick a choice from this dropdown")

    async def callback(self, i: Interaction[Red]) -> None:
        value = self.values[0]
        self.view.result = value
        self.view.stop()
        if not self.view.message:
            return
        with suppress(Exception):
            await self.view.message.edit(view=None)


class ChoiceView(ui.View):
    """
    This can be used in command converters where you offer a list of choices to the user
    and user need to pick an entry.
    """

    def __init__(
        self,
        *,
        options: list[SelectOption],
        timeout: float = 180,
    ) -> None:
        super().__init__(timeout=timeout)
        self.ctx: Context[Red] = MISSING
        self.message: Message = MISSING
        self.result: str | None = None
        self.add_item(OfferSelect(options=options))

    async def start(self, ctx: Context[Red], *, content: str, **kwargs) -> Message:
        self.ctx = ctx
        self.message = await ctx.send(content, view=self, **kwargs)
        return self.message

    async def on_timeout(self) -> None:
        self.stop()
        if not self.message:
            return
        with suppress(Exception):
            await self.message.edit(view=None)

    async def interaction_check(self, interaction: Interaction[Red]) -> bool:
        if interaction.user.id not in (*self.ctx.bot.owner_ids, self.ctx.author.id):
            await interaction.response.send_message("nuh uh", ephemeral=True)
            return False
        return True
