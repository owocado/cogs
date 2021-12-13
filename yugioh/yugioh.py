import asyncio
from typing import Any, Dict, Optional

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.menus import DEFAULT_CONTROLS, close_menu, menu


class YGO(commands.Cog):
    """Responds with info on a Yu-Gi-Oh! card."""

    __authors__ = "ow0x, dragonfire535"
    __version__ = "0.1.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    async def get(self, ctx, url: str) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.request("GET", url) as response:
                if response.status != 200:
                    await ctx.send(f"https://http.cat/{response.status}")
                    return None
                return await response.json()
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out.")
            return None

    @staticmethod
    def generate_embed(colour, footer, data) -> discord.Embed:
        embed = discord.Embed(colour=colour, title=data["name"], description=data["desc"])
        embed.url = f"https://db.ygoprodeck.com/card/?search={data['id']}"
        embed.set_author(
            name="Yu-Gi-Oh!", url="http://www.yugioh-card.com/en/", icon_url="https://i.imgur.com/AJNBflD.png",
        )
        embed.set_image(url=str(data["card_images"][0]["image_url"]))
        if "Monster" in data["type"]:
            embed.add_field(name="Attribute", value=str(data.get("attribute")))
            embed.add_field(name="Attack (ATK)", value=humanize_number(data.get("atk", 0)))
            link_value = "Link Value" if data["type"] == "Link Monster" else "Defense (DEF)"
            link_val = str(data.get("linkval")) if data["type"] == "Link Monster" else humanize_number(data["def"])
            embed.add_field(name=link_value, value=link_val)
        if data.get("card_sets"):
            card_sets = "".join(
                f"`[{str(i).zfill(2)}]` **{sets['set_name']}** (${sets['set_price']}) "
                f"{sets.get('set_rarity_code', '')}\n"
                for i, sets in enumerate(data["card_sets"], 1)
            )
            embed.add_field(name="Card Sets", value=card_sets, inline=False)
        price_dict = data["card_prices"][0]
        card_prices = (
            f"Cardmarket: **€{price_dict['cardmarket_price']}**\nTCGPlayer: **${price_dict['tcgplayer_price']}**\n"
            f"eBay: **${price_dict['ebay_price']}**\nAmazon: **${price_dict['amazon_price']}**\n"
        )
        embed.add_field(name="Prices", value=card_prices, inline=False)
        embed.set_footer(text=footer)
        return embed

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def ygocard(self, ctx: commands.Context, *, card_name: str):
        """Search for a Yu-Gi-Oh! card."""
        await ctx.trigger_typing()
        base_url = f"https://db.ygoprodeck.com/api/v7/cardinfo.php?fname={card_name}"
        card_data = await self.get(ctx, base_url)
        if not card_data: return
        if not card_data["data"]: return await ctx.send("No results.")

        pages = []
        for i, data in enumerate(card_data["data"], start=1):
            colour = await ctx.embed_colour()
            page_meta = f"Page {i} of {len(card_data['data'])} | Card Level: "
            race_or_spell = "Race:" if "Monster" in data["type"] else "Spell Type:"
            footer = f"{page_meta}{data.get('level', 'N/A')} | {race_or_spell}: {data['race']}"
            embed = self.generate_embed(colour, footer, data)
            pages.append(embed)

        controls = {"❌": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=60.0)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def randomcard(self, ctx: commands.Context):
        """Fetch a random Yu-Gi-Oh! card."""
        await ctx.trigger_typing()
        base_url = "https://db.ygoprodeck.com/api/v7/randomcard.php"
        data = await self.get(ctx, base_url)
        if not data: return
        colour = await ctx.embed_colour()
        race_or_spell = "Race" if "Monster" in data["type"] else "Spell Type"
        page_meta = f"ID: {data['id']} | Card Level: "
        footer = f"{page_meta}{data.get('level', 'N/A')} | {race_or_spell}: {data['race']}"
        embed = self.generate_embed(colour, footer, data)
        await ctx.send(embed=embed)
