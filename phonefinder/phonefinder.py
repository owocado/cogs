import asyncio
import urllib.parse
from contextlib import suppress
from io import BytesIO
from typing import Optional, cast

import aiohttp
import discord
from aiocache import SimpleMemoryCache, cached
from bs4 import BeautifulSoup as bsp, element
from redbot.core import commands

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT = True
except ModuleNotFoundError:
    PLAYWRIGHT = False

BASE_URL = "https://www.gsmarena.com/results.php3?sQuickSearch=yes&sName={}"

HEAD = {
    "Accept": "text/html,application/xhtml+xml,application/xml",
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    " (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
}


class PhoneFinder(commands.Cog):
    """Fetch device specs for a (smart)phone model from GSMArena."""

    __author__, __version__ = ("Author: ow0x", "Cog Version: 1.1.1")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\n{self.__author__}\n{self.__version__}"

    def __init__(self, bot) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self) -> None:
        asyncio.create_task(self.session.close())

    @cached(ttl=86400, cache=SimpleMemoryCache)
    async def _fetch_href(self, ctx: commands.Context, query: str) -> Optional[str]:
        try:
            async with self.session.get(BASE_URL.format(query), headers=HEAD) as resp:
                if resp.status != 200:
                    return None
                data = await resp.text()
        except asyncio.TimeoutError:
            return None

        soup = bsp(data, "html.parser").find("div", {"class": "makers"})
        get_ul_div = cast(element.Tag, soup.find("ul"))
        makers = get_ul_div.find_all("li")
        if not makers:
            return None

        if len(makers) == 1:
            return makers[0].a["href"]

        items = "\n".join(
            f"**`[{i}]`** {x.span.get_text(separator=' ')}" for i, x in enumerate(makers, 1)
        )

        choices = f"Found above {len(makers)} result(s). Pick one within 60 seconds!"
        embed = discord.Embed(description=items).set_footer(text=choices)
        prompt = await ctx.send(embed=embed)

        def check(msg) -> bool:
            return bool(
                msg.content.isdigit() and int(msg.content) in range(len(items) + 1)
                and msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id
            )

        try:
            choice = await ctx.bot.wait_for("message", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            choice = None

        if choice is None or choice.content.strip() == "0":
            with suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            return "0"
        else:
            choice = int(choice.content.strip()) - 1
            with suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            return makers[choice].a["href"]

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def phone(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch device specs, metadata for a (smart)phone model."""
        endpoint = await self._fetch_href(ctx=ctx, query=urllib.parse.quote(query))
        if endpoint == "0":
            return await ctx.send("OK! Operation cancelled.")
        if not endpoint:
            return await ctx.send("No results found for your query.")

        await ctx.trigger_typing()
        url = f"https://www.gsmarena.com/{endpoint}"

        try:
            async with self.session.get(url, headers=HEAD) as response:
                if response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                html = await response.text()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        soup = bsp(html, features="html.parser")
        html_title = soup.find_all("title")[0].text

        # You probably got temporary IP banned by GSM Arena
        if "Too" in html_title:
            return await ctx.send(html_title)

        def get_spec(query: str, key: str = "data-spec", class_: str = "td"):
            result = soup.find(class_, {key: query})
            return result.text if result else "N/A"

        embed = discord.Embed(colour=await ctx.embed_colour())
        embed.title = str(get_spec("specs-phone-name-title", "class", "h1"))
        embed.url = url
        embed.set_author(name="GSM Arena", icon_url="https://i.imgur.com/lYfT1kn.png")
        phone_thumb = cast(element.Tag, soup.find("div", {"class": "specs-photo-main"}))
        if phone_thumb:
            embed.set_thumbnail(url=str(phone_thumb.img.get("src")))

        overview = (
            f"🗓 › **{get_spec('released-hl', class_='span')}**\n\n"
            f"📱  **OS**: {get_spec('os-hl', class_='span')}\n"
            f"•  **Body**: {get_spec('body-hl', class_='span')}\n"
            f"•  **Internal**: {get_spec('internalmemory')}\n"
            f"•  **Storage Type**: {get_spec('memoryother')}\n\n"
            f"•  **Chipset:** {get_spec('chipset')}\n"
            f"•  **CPU**: {get_spec('cpu')}\n"
            f"•  **GPU**: {get_spec('gpu')}\n"
            f"•  **Battery**: {get_spec('batdescription1')}\n\n"
        )
        display = (
            f"**Type:** {get_spec('displaytype')}\n"
            f"**Size:** {get_spec('displaysize')}\n"
            f"**Resolution:** {get_spec('displayresolution')}\n"
            f"**Protection:** {get_spec('displayprotection')}\n"
        )
        mode = get_spec("cam1modules").replace("\n", " »  ")
        main_camera = (
            f"**Mode**: {mode}\n"
            f"**Features**: {get_spec('cam1features')}\n"
            f"**Video**: {get_spec('cam1video')}\n\n"
        )
        selfie_camera = (
            f"**Mode**: {get_spec('cam2modules')}\n"
            f"**Features**: {get_spec('cam2features')}\n"
            f"**Video**: {get_spec('cam2video')}\n\n"
        )
        misc_comms = (
            f"**WLAN**: {get_spec('wlan')}\n"
            f"**Bluetooth**: {get_spec('bluetooth')}\n"
            f"**GPS**: {get_spec('gps')}\n"
            f"**USB**: {get_spec('usb')}\n"
            f"**NFC**: {get_spec('nfc')}\n"
            f"**Sensors**: {get_spec('sensors')}\n\n"
        )
        sar = f"• **SAR US**: {get_spec('sar-us')}\n" + f"• **SAR EU**: {get_spec('sar-eu')}"

        embed.description = overview + sar
        embed.add_field(name="📱   DISPLAY:", value=display, inline=False)
        embed.add_field(name="📸   MAIN CAMERA:", value=main_camera, inline=False)
        embed.add_field(name="📷   SELFIE CAMERA:", value=selfie_camera, inline=False)
        embed.add_field(name="📡   MISC. COMMS:", value=misc_comms, inline=False)
        fans = get_spec("help-fans", key="class", class_="li").split("\n")[2]
        hits = cast(element.Tag, soup.find("li", {"class": "help-popularity"}))
        embed.set_footer(
            text=f"Fans: {fans} • Popularity: 📈 +{hits.strong.text} ({hits.span.text})"
        )
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(lambda ctx: PLAYWRIGHT)
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 90, commands.BucketType.default)
    async def phonespecs(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch device specs for a (smart)phone model in fancy image mode."""
        endpoint = await self._fetch_href(ctx=ctx, query=urllib.parse.quote(query))
        if endpoint == "0":
            return await ctx.send("OK! Operation cancelled.")
        if not endpoint:
            return await ctx.send("No results found for your query.")

        async with ctx.typing():
            url = f"https://www.gsmarena.com/{endpoint}"
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(channel="chrome")
                page = await browser.new_page(
                    color_scheme="dark",
                    screen={"width": 1920, "height": 1080},
                    viewport={"width": 1920, "height": 1080},
                )
                await page.goto(url)
                img_bytes = await page.locator('//*[@id="body"]/div/div[1]/div').screenshot()
                temp_1 = BytesIO(img_bytes)
                temp_1.seek(0)
                file_1 = discord.File(temp_1, "header.png")
                temp_1.close()

                specs_bytes = await page.locator('//*[@id="specs-list"]').screenshot()
                temp_2 = BytesIO(specs_bytes)
                temp_2.seek(0)
                file_2 = discord.File(temp_2, "main_specs.png")
                temp_2.close()

                await browser.close()

            em_1 = discord.Embed(colour=discord.Colour.random())
            em_1.set_image(url="attachment://header.png")
            await ctx.send(embed=em_1, file=file_1)
            em_2 = discord.Embed(colour=discord.Colour.random())
            em_2.set_image(url="attachment://main_specs.png")
            return await ctx.send(embed=em_2, file=file_2)
