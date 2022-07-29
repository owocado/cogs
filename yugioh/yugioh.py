import asyncio

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .api import NotFound, YuGiOhData


class YGO(commands.Cog):
    """Get nerdy info on a Yu-Gi-Oh! card or pull a random card."""

    __authors__ = ["ow0x", "dragonfire535"]
    __version__ = "2.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(self.__authors__)}\n"
            f"**Cog version:**  v{self.__version__}"
        )

    session = aiohttp.ClientSession()

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    def cog_unload(self) -> None:
        if self.session:
            asyncio.create_task(self.session.close())

    @staticmethod
    def generate_embed(data: YuGiOhData, colour: discord.Colour, footer: str) -> discord.Embed:
        embed = discord.Embed(colour=colour, title=data.name, description=data.desc)
        embed.url = f"https://db.ygoprodeck.com/card/?search={data.id}"
        embed.set_image(url=data.card_images[0].image_url)
        if "Monster" in data.type:
            embed.add_field(name="Attribute", value=str(data.attribute))
            embed.add_field(name="Attack (ATK)", value=humanize_number(data.attack))
            is_monster = data.type == "Link Monster"
            link_name = "Link Value" if is_monster else "Defense (DEF)"
            link_value = data.linkval if is_monster else humanize_number(data.defense)
            embed.add_field(name=link_name, value=str(link_value))
        if data.card_sets:
            card_sets = "\n".join(
                f"`[{i:>2}]`  {card.set_name} @ **${card.set_price}** {card.set_rarity_code}"
                for i, card in enumerate(data.card_sets, 1)
            )
            embed.add_field(name="Card Sets", value=card_sets, inline=False)
        if data.card_prices:
            card_prices = (
                f"Cardmarket: **€{data.card_prices[0].cardmarket_price}**\n"
                f"TCGPlayer: **${data.card_prices[0].tcgplayer_price}**\n"
                f"eBay: **${data.card_prices[0].ebay_price}**\n"
                f"Amazon: **${data.card_prices[0].amazon_price}**\n"
            )
            embed.add_field(name="Prices", value=card_prices, inline=False)
        embed.set_footer(text=footer, icon_url="https://i.imgur.com/AJNBflD.png")
        return embed

    @commands.command(aliases=("ygo", "yugioh"))
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def ygocard(self, ctx: commands.Context, *, card_name: str):
        """Search for a Yu-Gi-Oh! card."""
        async with ctx.typing():
            card = card_name.replace(" ", "%20")
            base_url = f"https://db.ygoprodeck.com/api/v7/cardinfo.php?fname={card}"
            card_data = await YuGiOhData.request(self.session, base_url)
            if isinstance(card_data, NotFound):
                return await ctx.send(str(card_data))

            pages = []
            for i, data in enumerate(card_data, start=1):
                colour = await ctx.embed_colour()
                page_meta = f"Page {i} of {len(card_data)} | Card Level: "
                race_or_spell = "Race" if "Monster" in data.type else "Spell Type"
                footer = f"{page_meta}{data.level} | {race_or_spell}: {data.race}"
                embed = self.generate_embed(data, colour, footer)
                pages.append(embed)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=90.0)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def randomcard(self, ctx: commands.Context):
        """Fetch a random Yu-Gi-Oh! card."""
        async with ctx.typing():
            base_url = "https://db.ygoprodeck.com/api/v7/randomcard.php"
            data = await YuGiOhData.request(self.session, base_url)
            if isinstance(data, NotFound):
                return await ctx.send(str(data))

            colour = await ctx.embed_colour()
            race_or_spell = "Race" if "Monster" in data.type else "Spell Type"
            page_meta = f"ID: {data.id} | Card Level: "
            footer = f"{page_meta}{data.level} | {race_or_spell}: {data.race}"
            embed = self.generate_embed(data, colour, footer)
            return await ctx.send(embed=embed)
