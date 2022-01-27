import asyncio
import contextlib
from datetime import datetime
from typing import Any, List, Optional

import aiohttp
import discord
from html2text import html2text
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import bold, humanize_number
from redbot.core.utils.menus import DEFAULT_CONTROLS, close_menu, menu
# from redbot.core.utils.dpy2_menus import BaseMenu, ListPages

from .stores import STORES

USER_AGENT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    " (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
}


class SteamCog(commands.Cog):
    """Get some info about a Steam game and fetch cheap game deals for PC game(s)."""

    __author__, __version__ = ("Author: ow0x", "Cog Version: 1.0.1")

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        pass

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\n{self.__author__}\n{self.__version__}"

    def __init__(self, bot: Red):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.emojis = self.bot.loop.create_task(self.init())

    def cog_unload(self):
        if self.emojis:
            self.emojis.cancel()
        asyncio.create_task(self.session.close())

    # Credits to someone, unfortunately
    async def init(self):
        await self.bot.wait_until_ready()
        self.platform_emojis = {
            "windows": discord.utils.get(self.bot.emojis, id=501562795880349696),
            "mac": discord.utils.get(self.bot.emojis, id=501561088815661066),
            "linux": discord.utils.get(self.bot.emojis, id=501561148156542996),
        }

    def timestamp(self, date_string: str) -> str:
        try:
            time_obj = datetime.strptime(date_string, "%b %d, %Y")
        except ValueError:
            time_obj = datetime.strptime(date_string, "%d %b, %Y")
        return f"<t:{int(time_obj.timestamp())}:R>"

    async def get(self, url: str, params) -> Optional[Any]:
        try:
            async with self.session.get(url, params=params, headers=USER_AGENT) as resp:
                return None if resp.status != 200 else await resp.json()
        except asyncio.TimeoutError: return None

    # Attribution: https://github.com/TrustyJAID/Trusty-cogs/blob/master/notsobot/notsobot.py#L212
    # at least my parents taught to me to give credits where it is due, unlike a snowflake's LOL!
    async def fetch_steam_game_id(self, ctx: commands.Context, query: str) -> Optional[int]:
        url = "https://store.steampowered.com/api/storesearch"
        data = await self.get(url, {"cc": "us", "l": "en", "term": query})
        if not data: return None
        if data.get("total", 0) == 0: return None
        elif data.get("total") == 1: return data.get("items")[0].get("id")
        else:
            # Attribution: https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
            items = "".join(f"**{i}.** {val.get('name')}\n" for i, val in enumerate(data.get("items"), 1))
            choices = f"Found multiple results for your query. Please select one from:\n\n{items}"
            send_to_channel = await ctx.send(choices)

            def check(msg):
                if (
                    msg.content.isdigit() and int(msg.content) in range(len(items) + 1)
                    and msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id
                ):
                    return True

            try:
                choice = await self.bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                choice = None
            if choice is None or choice.content.strip() == "0":
                with contextlib.suppress(discord.NotFound, discord.HTTPException):
                    await send_to_channel.edit("Operation cancelled.")
                return None
            else:
                with contextlib.suppress(discord.NotFound, discord.HTTPException):
                    await send_to_channel.delete()
                return data.get("items")[int(choice.content.strip()) - 1].get("id")

    @staticmethod
    def game_previews_embed(meta, data) -> discord.Embed:
        embed = discord.Embed(colour=meta[2], title=meta[4])
        embed.url = f"https://store.steampowered.com/app/{meta[3]}"
        embed.set_author(name="Steam", icon_url="https://i.imgur.com/xxr2UBZ.png")
        embed.set_image(url=data["path_full"])
        embed.set_footer(text=f"Preview {meta[0]} of {meta[1]}")
        return embed

    def steam_embed(self, meta, app) -> discord.Embed:
        em = discord.Embed(
            colour=meta[1], title=app["name"], description=app.get("short_description", ""),
        )
        em.url = f"https://store.steampowered.com/app/{meta[0]}"
        em.set_author(name="Steam", icon_url="https://i.imgur.com/xxr2UBZ.png")
        em.set_thumbnail(url=str(app.get("header_image")).replace("\\", ""))
        if app.get("price_overview"):
            em.add_field(name="Game Price", value=app["price_overview"].get("final_formatted"))
        if app.get("release_date").get("coming_soon"):
            em.add_field(name="Release Date", value="Coming Soon")
        else:
            em.add_field(name="Release Date", value=self.timestamp(app["release_date"].get("date")))
        if app.get("metacritic"):
            meta = app["metacritic"]
            metacritic = f"**{meta.get('score')}** ([Critic Reviews]({meta.get('url')}))"
            em.add_field(name="Metacritic Score", value=metacritic)
        if app.get("recommendations"):
            em.add_field(
                name="Recommendations", value=humanize_number(app["recommendations"].get("total")),
            )
        if app.get("achievements"):
            em.add_field(name="Achievements", value=app["achievements"].get("total"))
        if app.get("dlc"):
            em.add_field(name="DLC Count", value=len(app["dlc"]))
        if app.get("developers"):
            em.add_field(name="Developers", value=", ".join(app["developers"]))
        if app.get("publishers", [""]) != [""]:
            em.add_field(name="Publishers", value=", ".join(app["publishers"]))
        # thanks to npc203 (epic guy)
        platforms = ""
        if platform_dict := app.get("platforms"):
            for k, v in platform_dict.items():
                if v:
                    platforms += self.platform_emojis[k] or f"{k.title()} OS\n"
        if platforms:
            em.add_field(name="Supported Platforms", value=platforms)
        if app.get("genres"):
            genres = ", ".join(m.get("description", "") for m in app["genres"])
            em.add_field(name="Genres", value=genres)
        footer = "Click on reactions to browse through game previews\n"
        if app.get("content_descriptors").get("notes"):
            footer += f"Note: {app['content_descriptors']['notes']}"
        em.set_footer(text=footer)
        return em

    @commands.command(usage="name of steam game")
    @commands.bot_has_permissions(add_reactions=True, embed_links=True, read_message_history=True)
    async def steam(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch some useful info about a Steam game all from the comfort of your Discord home."""
        await ctx.trigger_typing()
        # TODO: remove this temp fix once game is released
        if query.lower() == "lost ark":
            app_id = 1599340
        else:
            app_id = await self.fetch_steam_game_id(ctx, query)

        if app_id is None: return await ctx.send("Could not find any results.")
        base_url = "https://store.steampowered.com/api/appdetails"
        data = await self.get(base_url, {"appids": app_id, "l": "en", "cc": "us", "json": 1})
        if not data: return await ctx.send("Something went wrong while querying Steam.")
        colour = await ctx.embed_colour()
        app_data = data[f"{app_id}"].get("data")
        pages = [self.steam_embed((app_id, colour), app_data)]
        if app_data.get("screenshots"):
            for i, preview in enumerate(app_data["screenshots"], start=1):
                meta = (i, len(app_data["screenshots"]), colour, app_id, app_data["name"])
                embed = self.game_previews_embed(meta, preview)
                pages.append(embed)

        controls = {"\u274c": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=90.0)
        # await BaseMenu(ListPages(pages), timeout=90, ctx=ctx).start(ctx)

    @staticmethod
    def gamereqs_embed(meta, app) -> List[discord.Embed]:
        pages = []
        platform_mapping = {
            "windows": "pc_requirements",
            "mac": "mac_requirements",
            "linux": "linux_requirements",
        }
        def sanitise(rawline):
            return html2text(rawline).replace("\n\n", "\n")
        for key, value in app.get("platforms").items():
            if value and app.get(platform_mapping[key]):
                em = discord.Embed(title=app["name"], colour=meta[1])
                em.url = f"https://store.steampowered.com/app/{meta[0]}"
                em.set_author(name="System Requirements")
                em.set_thumbnail(url=str(app.get("header_image")).replace("\\", ""))
                all_reqs = []
                if app[platform_mapping[key]].get("minimum"):
                    all_reqs.append(sanitise(app[platform_mapping[key]]["minimum"]))
                if app[platform_mapping[key]].get("recommended"):
                    all_reqs.append(sanitise(app[platform_mapping[key]]["recommended"]))
                em.description = "\n\n".join(all_reqs)
                em.set_footer(text="Powered by Steam", icon_url="https://i.imgur.com/xxr2UBZ.png")
                pages.append(em)
        return pages

    @commands.command(name="gamereqs", usage="name of steam game")
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def game_system_requirements(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch system requirements for a Steam game, both minimum and recommended if any."""
        await ctx.trigger_typing()
        app_id = await self.fetch_steam_game_id(ctx, query)
        if app_id is None:
            return await ctx.send("Could not find any results.")

        base_url = "https://store.steampowered.com/api/appdetails"
        data = await self.get(base_url, {"appids": app_id, "l": "en", "cc": "us", "json": 1})
        if not data: return await ctx.send("Something went wrong while querying Steam.")

        app_data = data[f"{app_id}"].get("data")
        meta = (app_id, await ctx.embed_colour())
        pages = self.gamereqs_embed(meta, app_data)
        if not pages:
            return await ctx.send("Hmmm, no system requirements found for this game on Steam!")

        controls = {"\u274c": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=60.0)
        # await BaseMenu(ListPages(pages), timeout=90, ctx=ctx).start(ctx)

    async def fetch_deal_id(self, ctx: commands.Context, query: str) -> Optional[int]:
        url = f"https://www.cheapshark.com/api/1.0/games?title={query}"
        data = await self.get(url, None)
        if not data: return None
        if len(data) == 0: return None
        elif len(data) == 1: return data[0].get("cheapestDealID")
        else:
            # Attribution: https://github.com/Sitryk/sitcogsv3/blob/master/lyrics/lyrics.py#L142
            items = "".join(f"**{i}.** {x.get('external')}\n" for i, x in enumerate(data[:20], 1))
            count = len(data) if len(data) <= 20 else 20
            choices = f"Please select one from below:\n\n{items}"
            send_to_channel = await ctx.send(f"Here are the first {count} results. {choices}")

            def check(msg):
                content = msg.content
                if (
                    msg.content.isdigit() and int(msg.content) in range(len(items) + 1)
                    and msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id
                ):
                    return True

            try:
                choice = await self.bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                choice = None

            if choice is None or choice.content.strip() == "0":
                await send_to_channel.delete()
                return None
            else:
                await send_to_channel.delete()
                return data[int(choice.content.strip()) - 1].get("cheapestDealID")

    @staticmethod
    def gamedeal_embed(stores, deal_id, data) -> discord.Embed:
        game = data["gameInfo"]
        em = discord.Embed(colour=discord.Colour.blurple(), title=game.get("name", ""))
        if game.get("steamAppID"):
            em.url = f"https://store.steampowered.com/app/{game.get('steamAppID')}"
        em.set_thumbnail(url=game.get("thumb"))
        mrp_price = game.get("retailPrice")
        deal_price = game.get("salePrice")
        em.add_field(name="Retail Price", value=f"~~{mrp_price} USD~~")
        discount = round(100 - ((float(deal_price) * 100) / float(mrp_price)))
        final_deal = f"**{deal_price} USD**\n({discount}% discount)"
        em.add_field(name="Deal Price", value=final_deal)
        base = "https://cheapshark.com/redirect?dealID="
        deal_store_info = f"[{bold(stores[game.get('storeID', '1')])}]({base}{deal_id})"
        em.add_field(name="Deal available on", value=deal_store_info)
        if game.get("steamRatingPercent") != "0" and game.get("steamRatingText"):
            steam_rating = f"{game.get('steamRatingPercent')}%\n({game.get('steamRatingText')})"
            em.add_field(name="Rating", value=steam_rating)
        if data.get("cheapestPrice") and data["cheapestPrice"].get("price"):
            date_from_epoch = datetime.utcfromtimestamp(data["cheapestPrice"]["date"]).timestamp()
            cheapest_price = (
                f"{data['cheapestPrice'].get('price')} USD\nthat was:\n<t:{int(date_from_epoch)}:R>"
            )
            em.add_field(name="Historical Cheapest Price", value=cheapest_price)
        if len(em.fields) == 5: em.add_field(name="\u200b", value="\u200b")
        em.set_footer(text="Data provided by cheapshark.com")
        return em

    @commands.command()
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def gamedeal(self, ctx: commands.Context, *, game_name: str) -> None:
        """Fetch cheapest deal for a PC game from cheaphark.com"""
        deal_id = await self.fetch_deal_id(ctx, game_name)
        if deal_id is None: return await ctx.send("No results.")

        await ctx.trigger_typing()
        deal_url = f"https://www.cheapshark.com/api/1.0/deals?id={deal_id}"
        data = await self.get(deal_url, None)
        if not data: return await ctx.send("Something went wrong while querying CheapShark!")
        all_stores = await self.get("https://www.cheapshark.com/api/1.0/stores", None)
        if all_stores:
            STORES = {x["storeID"]: x["storeName"] for x in all_stores}
        if data["gameInfo"].get("salePrice") == data["gameInfo"].get("retailPrice"):
            return await ctx.send("This game currently has no cheaper deals.")
        embed = self.gamedeal_embed(STORES, deal_id, data)
        await ctx.send(embed=embed)

    @staticmethod
    def latestdeals_embed(meta: tuple, stores, data) -> discord.Embed:
        em = discord.Embed(colour=meta[2])
        em.title = str(data["title"])
        if data.get("steamAppID"):
            em.url = f"https://store.steampowered.com/app/{data.get('steamAppID')}"
        em.set_thumbnail(url=data.get("thumb"))
        if data.get("salePrice") == data.get("normalPrice"):
            em.description = "This game currently has no cheaper deals."
        else:
            mrp_price = data.get("normalPrice")
            deal_price = data.get("salePrice")
            em.add_field(name="Retail Price", value=f"~~{mrp_price} USD~~")
            discount = round(float(data.get("savings")))
            final_deal = f"**{deal_price} USD**\n({discount}% discount)"
            em.add_field(name="Deal Price", value=final_deal)
            deal_store_info = (
                f"[{bold(stores[data.get('storeID')])}]"
                + f"(https://cheapshark.com/redirect?dealID={data['dealID']} 'Click here to go to this deal')"
            )
            em.add_field(name="Deal available on", value=deal_store_info)
        if data.get("steamRatingPercent") != "0" and data.get("steamRatingText"):
            steam_rating = f"{data.get('steamRatingPercent')}% ({data.get('steamRatingText')})"
            em.add_field(name="Rating", value=steam_rating)
        if len(em.fields) == 5: em.add_field(name="\u200b", value="\u200b")
        em.set_footer(text=f"Page {meta[0]} of {meta[1]} | Data provided by cheapshark.com")
        return em

    @commands.command()
    @commands.cooldown(1, 20, commands.BucketType.default)
    @commands.bot_has_permissions(add_reactions=True, embed_links=True, read_message_history=True)
    async def latestdeals(self, ctx: commands.Context, *, sort_by: str = "recent") -> None:
        """Fetch list of latest deals for games from cheapshark.com

        `sort_by` argument accepts only one of the following parameter:
        `deal rating`, `title`, `savings`, `price`, `metacritic`, `reviews`, `release`, `store`, `recent`
        """
        if sort_by not in [
            "title", "savings", "price", "metacritic", "reviews", "release", "store", "recent", "deal rating"
        ]:
            return await ctx.send("Invalid sorting option given. See commands help!")

        base_url = f"https://www.cheapshark.com/api/1.0/deals?sortBy={sort_by}"
        await ctx.trigger_typing()
        results = await self.get(base_url, None)
        all_stores = await self.get("https://www.cheapshark.com/api/1.0/stores", None)
        if all_stores:
            STORES = {x["storeID"]: x["storeName"] for x in all_stores}
        if not results: return await ctx.send("Something went wrong while querying CheapShark!")

        pages = []
        for i, data in enumerate(results, 1):
            meta = (i, len(results), await ctx.embed_color())
            em = self.latestdeals_embed(meta, STORES, data)
            pages.append(em)

        controls = {"\u274c": close_menu} if len(pages) == 1 else DEFAULT_CONTROLS
        await menu(ctx, pages, controls=controls, timeout=90.0)
        # await BaseMenu(ListPages(pages), timeout=90, ctx=ctx).start(ctx)
