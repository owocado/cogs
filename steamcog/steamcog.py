import asyncio
from datetime import datetime
from typing import Any, Dict, List

import aiohttp
import discord
from html2text import html2text
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list
from redbot.core.utils.menus import DEFAULT_CONTROLS, close_menu, menu

from .converter import GamedealsConverter, RegionConverter, QueryConverter, request
from .stores import AVAILABLE_REGIONS, STORES

CHEAPSHARK = "https://www.cheapshark.com"


class SteamCog(commands.Cog):
    """Fetch data on a Steam game and cheap game deals for PC game(s)."""

    __authors__ = ["ow0x"]
    __version__ = "2.0.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"Authors:  {', '.join(self.__authors__)}\n"
            f"Cog version:  v{self.__version__}"
        )

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, 357059159021060097, force_registration=True)
        default_user = {"region": None}
        self.config.register_user(**default_user)

    def cog_unload(self) -> None:
        asyncio.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    def timestamp(self, date_string: str) -> str:
        try:
            time_obj = datetime.strptime(date_string, "%b %d, %Y")
        except ValueError:
            time_obj = datetime.strptime(date_string, "%d %b, %Y")
        return f"<t:{int(time_obj.timestamp())}:R>"

    @staticmethod
    def game_previews_embed(image_url: str, **kwargs) -> discord.Embed:
        embed = discord.Embed(colour=kwargs["colour"], title=kwargs["title"])
        embed.url = f"https://store.steampowered.com/app/{kwargs['id']}"
        # embed.set_author(name="Steam", icon_url="https://i.imgur.com/xxr2UBZ.png")
        embed.set_image(url=image_url)
        return embed

    def steam_embed(self, app: Dict[str, Any], **kwargs) -> discord.Embed:
        em = discord.Embed(colour=kwargs["colour"], title=app["name"])
        em.url = f"https://store.steampowered.com/app/{kwargs['id']}"
        # em.set_author(name="Steam", icon_url="https://i.imgur.com/xxr2UBZ.png")
        em.set_image(url=(app.get("header_image") or "").replace("\\", ""))
        summary = app.get("short_description") or ""

        if msrp := app.get("price_overview", {}):
            summary += (
                "\n\n↗ **[See the regional price chart on SteamDB!]"
                f"(https://steamdb.info/app/{kwargs['id']}/)**"
            )
            if (discount := msrp.get("discount_percent")) and (
                initial := msrp.get("initial_formatted")
            ):
                discount = f"~~{initial}~~\n{msrp.get('final_formatted')}\n({discount}% discount)"
                em.add_field(name=f"Price (in {msrp['currency']})", value=discount)
            else:
                em.add_field(
                    name=f"Price (in {msrp['currency']})", value=msrp.get("final_formatted")
                )
        if app.get("release_date", {}).get("coming_soon"):
            em.add_field(name="Release Date", value="Coming Soon")
        else:
            em.add_field(
                name="Release Date", value=self.timestamp(app["release_date"].get("date"))
            )
        if meta_ := app.get("metacritic", {}):
            metacritic = f"**{meta_.get('score')}%** ([Critic Reviews]({meta_.get('url')}))"
            em.add_field(name="Metacritic Score", value=metacritic)
        if recommend := app.get("recommendations"):
            em.add_field(name="Recommendations", value=f'{recommend.get("total"):,}')
        if achievements := app.get("achievements"):
            em.add_field(name="Achievements", value=achievements.get("total"))
        if app.get("dlc"):
            em.add_field(name="DLC Count", value=len(app["dlc"]))
        # thanks to npc203 (epic guy)
        platforms = []
        platform_emojis = {
            "windows": str(discord.utils.get(self.bot.emojis, id=501562795880349696) or "Windows"),
            "mac": str(discord.utils.get(self.bot.emojis, id=501561088815661066) or "Mac OS"),
            "linux": str(discord.utils.get(self.bot.emojis, id=501561148156542996) or "Linux"),
        }
        if platform_dict := app.get("platforms", {}):
            for key, value in platform_dict.items():
                if value:
                    platforms.append(platform_emojis[key])
        if platforms:
            em.add_field(name="Supported Platforms", value=", ".join(platforms))
        if developers := app.get("developers"):
            em.add_field(name="Developers", value=", ".join(developers))
        if (publishers := app.get("publishers")) and (joined := humanize_list(publishers)):
            em.add_field(name="Publishers", value=joined)
        if genres := app.get("genres"):
            em.add_field(
                name="Genres", value=", ".join(map(lambda x: x.get("description") or "", genres))
            )
        if len(em.fields) in {5, 8, 11}:
            em.add_field(name="\u200b", value="\u200b")
        if (content := app.get("content_descriptors", {})) and (note := content.get("notes")):
            em.add_field(name="🔞 MATURE CONTENT DESCRIPTION", value=note, inline=False)
        em.description = summary
        em.set_footer(
            text="Click on reactions to browse game preview screenshots!",
            icon_url="https://i.imgur.com/xxr2UBZ.png",
        )
        return em

    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def steam(self, ctx: commands.Context, *, query: QueryConverter):
        """
        Fetch basic info about a game available on Valve Steam store.

        To get game pricing for your region, use `[p]steam setmyregion <region>`.
        You can provide either an [ISO3166 alpha-2](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes) region code or the country name.
        Once set, the bot will show pricing for your region in command embed.
        """
        async with ctx.typing():
            # TODO: remove this temp fix once game is released
            base_url = "https://store.steampowered.com/api/appdetails"
            user_region = (await self.config.user(ctx.author).region()) or "US"
            data = await request(
                base_url, params={"appids": str(query), "l": "en", "cc": user_region, "json": "1"}
            )
            if type(data) == int:
                await ctx.send(f"⚠ API sent response code: https://http.cat/{data}")
                return
            if not data:
                return await ctx.send("Something went wrong while querying Steam.")
            colour = await ctx.embed_colour()
            app_data = data[f"{query}"].get("data")

            pages = [self.steam_embed(app_data, id=query, colour=colour)]
            if screenshots := app_data.get("screenshots"):
                for i, preview in enumerate(screenshots, start=1):
                    embed = self.game_previews_embed(
                        preview.get("path_full") or "",
                        colour=colour,
                        id=query,
                        title=app_data["name"],
                    )
                    embed.set_footer(
                        text=f"Preview {i} of {len(app_data['screenshots'])}",
                        icon_url="https://i.imgur.com/xxr2UBZ.png",
                    )
                    pages.append(embed)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=90.0)

    @steam.command(name="setmyregion")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def steam_set_my_region(self, ctx: commands.Context, *, region: RegionConverter):
        """Set your Steam region/country to show localized pricing.

        If set, I will show game price for your region in `[p]steam` command embed.
        If not available, the price will default to USD.

        You can provide either an [ISO3166 alpha-2](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes) region code or the valid country name.

        **Example:**
            - `[p]steam setmyregion DE`
            - `[p]steam setmyregion United States`
        """
        country_name = [k for k, v in AVAILABLE_REGIONS.items() if v == region]
        user_region = await self.config.user(ctx.author).region()
        action = "changed to" if user_region else "set to"
        await self.config.user(ctx.author).region.set(region)
        await ctx.send(
            f"✅ Success! Your region has now been {action} :flag_{region.lower()}:"
            f" **{country_name[0].replace('_', ' ').title()}**!\n"
            f"It will be used to show game price for your set region"
            f" in `{ctx.clean_prefix}steam` command embeds from now.\n"
            "If not available, the price will default to USD otherwise.\n"
            # "You can change your region later using `[p]steam setmyregion <region>`."
        )

    @staticmethod
    def game_requirements_embed(app: Dict[str, Any], **kwargs) -> List[discord.Embed]:
        pages = []
        platform_mapping = {
            "windows": "pc_requirements",
            "mac": "mac_requirements",
            "linux": "linux_requirements",
        }

        all_platforms: Dict[str, str] = app.get("platforms", {})
        index = 0
        for key, value in all_platforms.items():
            if value and app.get(platform_mapping[key]):
                index += 1
                em = discord.Embed(title=app["name"], colour=kwargs["colour"])
                em.url = f"https://store.steampowered.com/app/{kwargs['id']}"
                em.set_author(name="System Requirements")
                em.set_thumbnail(url=(app.get("header_image") or "").replace("\\", ""))
                all_reqs = []
                if minimum := app[platform_mapping[key]].get("minimum"):
                    all_reqs.append(html2text(minimum).replace("\n\n", "\n"))
                if recommended := app[platform_mapping[key]].get("recommended"):
                    all_reqs.append(html2text(recommended).replace("\n\n", "\n"))
                em.description = "\n\n".join(all_reqs)
                em.set_footer(
                    text=f"Page {index} • Data provided by Steam",
                    icon_url="https://i.imgur.com/xxr2UBZ.png",
                )
                pages.append(em)
        return pages

    @commands.command(name="gamereqs", usage="name of steam game")
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def game_system_requirements(self, ctx: commands.Context, *, query: QueryConverter):
        """Fetch system requirements for a Steam game, both minimum and recommended if any."""
        async with ctx.typing():
            base_url = "https://store.steampowered.com/api/appdetails"
            user_region = (await self.config.user(ctx.author).region()) or "US"
            data = await request(
                base_url, params={"appids": str(query), "l": "en", "cc": user_region, "json": "1"}
            )
            if type(data) == int:
                await ctx.send(f"⚠ API sent response code: https://http.cat/{data}")
                return
            if not data:
                return await ctx.send("Something went wrong while querying Steam.")

            app_data = data[f"{query}"].get("data")
            pages = self.game_requirements_embed(
                app_data, colour=await ctx.embed_colour(), id=query
            )
            if not pages:
                await ctx.send("Hmmm, no system requirements info found for this game on Steam!")
                return

        controls = {"\N{CROSS MARK}": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=90.0)

    @staticmethod
    def gamedeal_embed(stores, deal_id: str, data: Dict[str, Any]) -> discord.Embed:
        game = data["gameInfo"]
        em = discord.Embed(colour=discord.Colour.blurple(), title=game.get("name") or "")
        if game.get("steamAppID"):
            em.url = f"https://store.steampowered.com/app/{game['steamAppID']}"
        em.set_thumbnail(url=game.get("thumb"))
        mrp_price = game.get("retailPrice")
        deal_price = game.get("salePrice")
        em.add_field(name="Retail Price", value=f"~~{mrp_price} USD~~")
        discount = round(100 - ((float(deal_price) * 100) / float(mrp_price)))
        final_deal = f"**{deal_price} USD**\n({discount}% discount)"
        em.add_field(name="Deal Price", value=final_deal)
        if storeID := game.get("storeID"):
            em.add_field(
                name="Deal available on",
                value=f"[{stores[storeID]}]({CHEAPSHARK}/redirect?dealID={deal_id})",
            )
        if (rating := game.get("steamRatingPercent")) and (review := game.get("steamRatingText")):
            em.add_field(name="Rating", value=f"{rating}%\n({review})")
        if (topdeal := data.get("cheapestPrice")) and (cheapest := topdeal.get("price")):
            date_from_epoch = datetime.utcfromtimestamp(topdeal["date"]).timestamp()
            cheapest_price = f"{cheapest} USD\nthat was:\n<t:{int(date_from_epoch)}:R>"
            em.add_field(name="Historical Cheapest Price", value=cheapest_price)
        if len(em.fields) == 5:
            em.add_field(name="\u200b", value="\u200b")
        em.set_footer(text="Data provided by CheapShark API")
        return em

    @commands.command()
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def gamedeal(self, ctx: commands.Context, *, query: GamedealsConverter):
        """Fetch cheapest deal for a PC game from cheaphark.com"""
        async with ctx.typing():
            data = await request(f"{CHEAPSHARK}/api/1.0/deals?id={query}")
            if type(data) == int:
                await ctx.send(f"⚠ API sent response code: https://http.cat/{data}")
                return
            if not data:
                return await ctx.send("\u26d4 Could not query CheapShark API!")

            all_stores = await request(f"{CHEAPSHARK}/api/1.0/stores")
            NEW_STORES = None
            if all_stores and type(all_stores) == list:
                NEW_STORES = {x["storeID"]: x["storeName"] for x in all_stores}
            if data["gameInfo"].get("salePrice") == data["gameInfo"].get("retailPrice"):
                return await ctx.send("This game currently has no cheaper deals.")
            embed = self.gamedeal_embed(NEW_STORES or STORES, query, data)
            return await ctx.send(embed=embed)

    @staticmethod
    def latestdeals_embed(data: Dict[str, Any], **kwargs) -> discord.Embed:
        em = discord.Embed(colour=kwargs["colour"])
        em.title = str(data["title"])
        if data.get("steamAppID"):
            em.url = f"https://store.steampowered.com/app/{data.get('steamAppID')}"
        em.set_thumbnail(url=data.get("thumb"))
        if data.get("salePrice") == data.get("normalPrice"):
            em.description = "This game currently has no cheaper deals."
        else:
            mrp_price = data.get("normalPrice")
            deal_price = (
                f"{data['salePrice']} USD" if data.get("salePrice", 0.0) > 0.0 else "🎉 FREE"
            )
            em.add_field(name="Retail Price", value=f"~~{mrp_price} USD~~")
            discount = round(float(data.get("savings", 0)))
            final_deal = f"**{deal_price}**\n({discount}% discount)"
            em.add_field(name="Deal Price", value=final_deal)
            deal_store_info = (
                f"[**{kwargs['stores'][data.get('storeID')]}**]({CHEAPSHARK}/"
                f"redirect?dealID={data['dealID']} 'Click here to go to this deal')"
            )
            em.add_field(name="Deal available on", value=deal_store_info)
        if (rating := data.get("steamRatingPercent")) and (review := data.get("steamRatingText")):
            em.add_field(name="Rating", value=f"{rating}% ({review})")
        if len(em.fields) == 5:
            em.add_field(name="\u200b", value="\u200b")
        em.set_footer(
            text=f"Page {kwargs['page']} of {kwargs['pages']} • Data provided by CheapShark API"
        )
        return em

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.default)
    @commands.bot_has_permissions(add_reactions=True, embed_links=True, read_message_history=True)
    async def latestdeals(self, ctx: commands.Context, *, sort_by: str = "savings"):
        """Fetch list of latest games deals from cheapshark API

        `sort_by` argument accepts only any from below options:
        `deal rating`, `title`, `savings`, `price`, `metacritic`, `reviews`, `release`, `store`, `recent`
        """
        allowed_sorts = [
            "title",
            "savings",
            "price",
            "metacritic",
            "reviews",
            "release",
            "store",
            "recent",
            "deal rating",
        ]
        if sort_by.lower() not in allowed_sorts:
            return await ctx.send_help()

        async with ctx.typing():
            result = await request(f"{CHEAPSHARK}/api/1.0/deals?sortBy={sort_by.lower()}")
            if type(result) == int:
                await ctx.send(f"⚠ API sent response code: https://http.cat/{result}")
                return
            if not result:
                return await ctx.send("\u26d4 Could not query CheapShark API!")

            all_stores = await request(f"{CHEAPSHARK}/api/1.0/stores")
            NEW_STORES = None
            if all_stores and type(all_stores) == list:
                NEW_STORES = {x["storeID"]: x["storeName"] for x in all_stores}

            pages = []
            for i, data in enumerate(result, 1):
                em = self.latestdeals_embed(
                    data,
                    stores=NEW_STORES or STORES,
                    colour=await ctx.embed_color(),
                    page=i,
                    pages=len(result),
                )
                pages.append(em)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=90.0)
