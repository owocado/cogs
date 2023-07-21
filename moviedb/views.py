from contextlib import suppress
from typing import TYPE_CHECKING, Any, Dict, List

import discord
from redbot.core import commands
from redbot.core.utils.views import BaseMenu, ListPages

if TYPE_CHECKING:
    from .moviedb import MovieDB

GENDERS = {
    "0": "",
    "1": "\u2640 Female",
    "2": "\u2642 Male",
}


class MovieView(discord.ui.View):

    def __init__(self, timeout: int, **kwargs):
        super().__init__(timeout=timeout)
        self.banner: str = kwargs.get("banner")
        self.cog: MovieDB = kwargs.get("cog")
        self.ctx: commands.Context = kwargs.get("ctx")
        self.colour: discord.Colour = kwargs.get("colour")
        self.message: discord.Message = kwargs.get("message")
        self.movie_id: int = kwargs.get("movie_id")

    async def on_timeout(self):
        self.stop()
        for item in self.children:
            item.disabled = True
        with suppress(discord.NotFound, discord.HTTPException):
            await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        await interaction.response.defer()
        return True

    @discord.ui.button(label="Movie Banner", style=discord.ButtonStyle.gray)
    async def banner_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = discord.Embed(colour=self.colour)
        emb.set_image(url=self.banner)
        await interaction.followup.send(embeds=[emb], ephemeral=True)

    @discord.ui.button(label="Cast", style=discord.ButtonStyle.blurple)
    async def movie_cast(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.followup.send(
                f"Only {interaction.user} can control this button.",
                ephemeral=True
            )

        base_url = f"https://api.themoviedb.org/3/movie/{self.movie_id}/credits"
        key = (await self.ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        credits = await self.cog.get(base_url, {"api_key": key})
        if not credits:
            return await interaction.followup.send(
                "Oh no! No data received from API.",
                ephemeral=True
            )

        full_cast: List[Dict[str, Any]] = credits.get("cast")
        chunked = list(discord.utils.as_chunks(full_cast, 3))
        pages = []
        for i, entries in enumerate(chunked, 1):
            embeds = []
            for obj in entries:
                emb = discord.Embed(colour=discord.Colour.random())
                emb.title = obj.get("original_name")
                emb.url = f"https://www.themoviedb.org/person/{obj['id']}"
                emb.description = f"as **{obj.get('character')}**\n{GENDERS[str(obj.get('gender', 0))]}"
                if obj.get("profile_path"):
                    emb.set_thumbnail(
                        url=f"https://image.tmdb.org/t/p/original{obj['profile_path']}"
                    )
                emb.set_footer(text="\u3000\u200b"*25)
                embeds.append(emb)

            pages.append({"embeds": embeds})

        button.disabled = True
        with suppress(discord.NotFound):
            await self.message.edit(view=self)
        return await BaseMenu(ListPages(pages), timeout=99, ctx=self.ctx).start(self.ctx)

