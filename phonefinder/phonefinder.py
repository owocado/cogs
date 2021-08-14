import asyncio
from contextlib import suppress
from urllib.parse import quote

import aiohttp
import discord
from aiocache import SimpleMemoryCache, cached
from bs4 import BeautifulSoup as bsp, element
from redbot.core import commands

BASE_URL = "https://www.gsmarena.com/results.php3?sQuickSearch=yes&sName={}"

HEAD = {
    "Accept": "text/html,application/xhtml+xml,application/xml",
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
}


class PhoneFinder(commands.Cog):
    """Fetch device specs for a (smart)phone model from GSMArena."""

    __author__ = "ow0x"
    __version__ = "1.0.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @cached(ttl=86400, cache=SimpleMemoryCache)
    async def fetch_href(self, ctx, query: str):
        try:
            async with self.session.get(BASE_URL.format(query), headers=HEAD) as resp:
                if resp.status != 200:
                    return None
                data = await resp.text()
        except asyncio.TimeoutError:
            return None

        soup = bsp(data, "html.parser").find('div', {'class': "makers"})
        makers = soup.find("ul").find_all("li")
        if not makers:
            return None

        if len(makers) == 1:
            return makers[0].a["href"]

        items = ""
        for i, x in enumerate(makers, start=1):
            items += f"`[{i}]` {x.span.get_text(separator=' ')}\n"

        choices = f"Found below **{len(makers)}** result(s). Pick one from:\n\n" + items
        prompt = await ctx.send(choices)

        def check(msg):
            content = msg.content
            if (
                content.isdigit()
                and int(content) in range(0, len(items) + 1)
                and msg.author.id == ctx.author.id
                and msg.channel.id == ctx.channel.id
            ):
                return True

        try:
            choice = await self.bot.wait_for("message", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            choice = None

        if choice is None or choice.content.strip() == "0":
            with suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            return 0
        else:
            choice = choice.content.strip()
            choice = int(choice) - 1
            href = makers[choice].a["href"]
            with suppress(discord.NotFound, discord.HTTPException):
                await prompt.delete()
            return href

    @commands.command()
    @commands.bot_has_permissions(embed_links=True, read_message_history=True)
    async def phone(self, ctx: commands.Context, *, query: str):
        """Fetch device specs and other metadata about a (smart)phone model."""
        endpoint = await self.fetch_href(ctx=ctx, query=quote(query))
        if endpoint == 0:
            return await ctx.send("OK! Operation cancelled.")
        if not endpoint:
            return await ctx.send("No results found for your query.")

        await ctx.trigger_typing()
        url = f"https://www.gsmarena.com/{endpoint}"
        try:
            async with self.session.get(url, headers=HEAD) as response:
                if response.status != 200:
                    return await ctx.send(f"https://http.cat/{response.status}")
                page = await response.text()
        except asyncio.TimeoutError:
            return await ctx.send("Operation timed out.")

        soup = bsp(page, features="html.parser")
        html_title = soup.find_all("title")[0].text

        # You probably got temporary IP banned by GSM Arena
        if "Too" in html_title:
            return await ctx.send(html_title)

        def get_spec(query: str, key: str = "data-spec", cls: str = "td"):
            result: element.Tag = soup.find(cls, {key: query})
            return result.text if result else "N/A"

        embed = discord.Embed(colour=await ctx.embed_colour())
        embed.title = str(get_spec("specs-phone-name-title", "class", "h1"))
        embed.url = url
        embed.set_author(name="GSM Arena", icon_url="https://i.imgur.com/zi7jVhF.png")
        phone_thumb: element.Tag = soup.find("div", {"class": "specs-photo-main"})
        if phone_thumb:
            embed.set_thumbnail(url=str(phone_thumb.img.get("src")))

        release_date = f"🗓 **{get_spec('released-hl', cls='span')}**\n"
        phone_os = f"📱 **OS**: {get_spec('os-hl', cls='span')}\n"
        in_memory = f"🤖 **Internal**: {get_spec('internalmemory')}\n"
        storage_type = f"🗄 **Storage Type**: {get_spec('memoryother')}\n\n"
        cpu = f"🧠 **CPU**: {get_spec('cpu')}\n"
        gpu = f"╰⇢ **GPU**: {get_spec('gpu')}\n"
        battery = f"🔋 **Battery**: {get_spec('batdescription1')}\n\n"
        overview = release_date + phone_os + in_memory + storage_type + cpu + gpu + battery
        main_camera = (
            "📸 **__MAIN CAMERA__**:\n"
            + f"• **Mode**: {get_spec('cam1modules')}\n"
            + f"• **Features**: {get_spec('cam1features')}\n"
            + f"• **Video**: {get_spec('cam1video')}\n\n"
        )
        selfie_camera = (
            "📷 **__SELFIE CAMERA__**:\n"
            + f"• **Mode**: {get_spec('cam2modules')}\n"
            + f"• **Features**: {get_spec('cam2features')}\n"
            + f"• **Video**: {get_spec('cam2video')}\n\n"
        )
        comms = (
            "📡 **__MISC. COMMS:__**\n"
            f"• **WLAN**: {get_spec('wlan')}\n"
            f"• **Bluetooth**: {get_spec('bluetooth')}\n"
            f"• **GPS**: {get_spec('gps')}\n"
            f"• **USB**: {get_spec('usb')}\n"
            f"• **NFC**: {get_spec('nfc')}\n"
            f"• **Sensors**: {get_spec('sensors')}\n\n"
        )
        sar = f"• **SAR US**: {get_spec('sar-us')}\n" + f"• **SAR EU**: {get_spec('sar-eu')}"

        embed.description = overview + main_camera + selfie_camera + comms + sar
        embed.add_field(name="Display Size", value=str(get_spec("displaysize-hl", cls="span")))
        embed.add_field(name="Resolution", value=str(get_spec("displayres-hl", cls="div")))
        embed.add_field(name="Chipset", value=str(get_spec("chipset-hl", cls="div")))
        fans = get_spec("help-fans", key="class", cls="li").split("\n")[2]
        hits: element.Tag = soup.find("li", {"class": "help-popularity"})
        embed.set_footer(
            text=f"Fans: {fans} • Popularity: 📈 +{hits.strong.text} ({hits.span.text})"
        )

        await ctx.send(embed=embed)
