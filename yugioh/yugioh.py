import asyncio

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu


class YGO(command.Cog):
    """Responds with info on a Yu-Gi-Oh! card."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def yugioh(self, ctx: commands.Context, *, card_name: str):
        """Search for a Yu-Gi-Oh! card."""
        await ctx.trigger_typing()
        base_url = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
        params = {"fname": card_name, "la": "english"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    card_data = await response.json()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        if not card_data["data"]:
            return await ctx.send("No results.")

        pages = []
        for i, data in enumerate(card_data["data"]):
            embed = discord.Embed(colour=await ctx.embed_colour())
            embed.title = data["name"]
            embed.url = f"https://db.ygoprodeck.com/card/?search={data['id']}"
            embed.description = data["desc"]
            embed.set_author(
                name="Yu-Gi-Oh!",
                url="http://www.yugioh-card.com/en/",
                icon_url="https://i.imgur.com/AJNBflD.png",
            )
            embed.set_image(url=str(data["card_images"][0]["image_url"]))
            race_or_spell = "Race" if "Monster" in data["type"] else "Spell Type"
            embed.add_field(name=race_or_spell, value=data["race"])
            if "Monster" in data["type"]:
                embed.add_field(name="Attribute", value=str(data.get("attribute")))
                embed.add_field(
                    name="Attack (ATK)", value=humanize_number(str(data.get("atk")))
                )
                embed.add_field(
                    name="Link Value"
                    if data["type"] == "Link Monster"
                    else "Defense (DEF)",
                    value=str(data.get("linkval"))
                    if data["type"] == "Link Monster"
                    else humanize_number(data["def"]),
                )
            card_sets = ""
            if data.get("card_sets"):
                for count, sets in enumerate(data["card_sets"]):
                    card_sets += "`[{}]` **{}** (${}) {}\n".format(
                        str(count + 1).zfill(2),
                        sets["set_name"],
                        sets["set_price"],
                        sets["set_rarity_code"],
                    )
                embed.add_field(name="Card Sets", value=card_sets, inline=False)
            price_dict = data["card_prices"][0]
            card_prices = (
                f"Cardmarket: **€{price_dict['cardmarket_price']}**\n"
                f"TCGPlayer: **${price_dict['tcgplayer_price']}**\n"
                f"eBay: **${price_dict['ebay_price']}**\n"
                f"Amazon: **${price_dict['amazon_price']}**\n"
                f"Coolstuff Inc.: **${price_dict['coolstuffinc_price']}**\n"
            )
            embed.add_field(name="Prices", value=card_prices, inline=False)
            embed.set_footer(
                text=f"Page {i + 1} of {len(card_data['data'])} | Card Level: {data.get('level', 'N/A')}"
            )
            pages.append(embed)

        if len(pages) == 1:
            return await ctx.send(embed=pages[0])
        else:
            await menu(ctx, pages, DEFAULT_CONTROLS, timeout=60.0)
