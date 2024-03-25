from random import choice
from typing import List, Literal

import discord
from redbot.core import Config, commands
from redbot.core.commands import Context

from .api.base import NotFound
from .api.character import CharacterData
from .api.media import MediaData
from .api.schedule import ScheduleData
from .api.staff import StaffData
from .api.studio import StudioData
from .api.user import UserData
from .converter import GenreTagFinder
from .embed_maker import (
    do_character_embed,
    do_media_embed,
    do_schedule_embed,
    do_staff_embed,
    do_studio_embed,
    do_user_embed,
)
from .schemas import (
    CHARACTER_SCHEMA,
    GENRE_SCHEMA,
    MEDIA_SCHEMA,
    SCHEDULE_SCHEMA,
    STAFF_SCHEMA,
    STUDIO_SCHEMA,
    TAG_SCHEMA,
    USER_SCHEMA,
)
from .tags import ANILIST_GENRES
from .views import WeebView


@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allow_contexts(guilds=True, dms=True, private_channels=True)
class Anilist(commands.GroupCog, group_name="anilist"):
    """Fetch info on anime, manga, character, studio and more from Anilist!"""

    __authors__ = "owocado (<@306810730055729152>)"
    __version__ = "2.9.0"

    def format_help_for_context(self, ctx: Context) -> str:
        """Thanks Sinbad"""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(self.__authors__)}\n"
            f"**Cog version:**  {self.__version__}"
        )

    def __init__(self) -> None:
        self.config = Config.get_conf(self, 306810730055729152, force_registration=True)
        self.config.register_guild(**{"SHOW_ADULT_MEDIA": None})

    async def to_hide_adult_media(self, ctx: Context) -> bool:
        guild_toggle = False
        nsfw_channel = True
        if ctx.guild:
            guild_toggle: bool = await self.config.guild(ctx.guild).SHOW_ADULT_MEDIA()
            nsfw_channel = ctx.channel.is_nsfw()
        return not guild_toggle and not nsfw_channel

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    @discord.app_commands.describe(query="Enter the name of the anime")
    async def anime(self, ctx: Context, *, query: str):
        """Fetch info on any anime from given query!"""
        await ctx.typing()
        results = await MediaData.request(
            ctx.bot.session, query=MEDIA_SCHEMA, search=query, type="ANIME", sort="TRENDING_DESC",
        )
        if isinstance(results, NotFound):
            await ctx.send(str(results), ephemeral=True)
            return

        pages: List[discord.Embed] = []
        for idx, page in enumerate(results, start=1):
            emb = do_media_embed(page, await self.to_hide_adult_media(ctx))
            text = f"{emb.footer.text} • Page {idx} of {len(results)}"
            emb.set_footer(text=text)
            pages.append(emb)
        if len(pages) == 1:
            await ctx.send(embed=pages[0])
            return
        view = WeebView(ctx=ctx, pages=pages, timeout=120, use_footer=True)
        view.message = await ctx.send(embed=pages[0], view=view)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=["manhwa"])
    @discord.app_commands.describe(query="Enter the name of manga")
    async def manga(self, ctx: Context, *, query: str):
        """Fetch info on any manga from given query!"""
        await ctx.typing()
        results = await MediaData.request(
            ctx.bot.session, query=MEDIA_SCHEMA, search=query, type="MANGA",
        )
        if isinstance(results, NotFound):
            await ctx.send(str(results), ephemeral=True)
            return

        pages = []
        for idx, page in enumerate(results, start=1):
            emb = do_media_embed(page, await self.to_hide_adult_media(ctx))
            emb.set_footer(text=f"{emb.footer.text} • Page {idx} of {len(results)}")
            pages.append(emb)
        if len(pages) == 1:
            await ctx.send(embed=pages[0])
            return
        view = WeebView(ctx=ctx, pages=pages, timeout=120, use_footer=True)
        view.message = await ctx.send(embed=pages[0], view=view)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    @discord.app_commands.describe(media_type="Choose one from given options")
    async def trending(self, ctx: Context, media_type: Literal["anime", "manga"]):
        """Fetch currently trending animes or manga from Anilist!"""
        await ctx.typing()
        results = await MediaData.request(
            ctx.bot.session, query=MEDIA_SCHEMA, type=media_type.upper(), sort="TRENDING_DESC"
        )
        if isinstance(results, NotFound):
            await ctx.send(str(results), ephemeral=True)
            return

        pages = []
        for idx, page in enumerate(results, start=1):
            emb = do_media_embed(page, await self.to_hide_adult_media(ctx))
            emb.set_footer(text=f"{emb.footer.text} • Page {idx} of {len(results)}")
            pages.append(emb)
        if len(pages) == 1:
            await ctx.send(embed=pages[0])
            return
        view = WeebView(ctx=ctx, pages=pages, timeout=120, use_footer=True)
        view.message = await ctx.send(embed=pages[0], view=view)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    @discord.app_commands.describe(media_type="Choose an option!")
    @discord.app_commands.describe(genre="e.g. action, drama, fantasy, mystery or thriller etc.")
    async def random(
        self,
        ctx: Context,
        media_type: Literal["anime", "manga"],
        *,
        genre: discord.app_commands.Transform[str, GenreTagFinder] = "",
    ):
        """Fetch a random anime or manga based on provided genre or tag!

        **Supported Genres:**
        - Action, Adventure, Comedy, Drama, Ecchi
        - Fantasy, Hentai, Horror, Mahou Shoujo, Mecha
        - Music, Mystery, Psychological, Romance, Sci-Fi
        - Slice of Life, Sports, Supernatural, Thriller

        You can also use any of the search tags supported on Anilist as well!
        """
        await ctx.typing(ephemeral=bool(ctx.guild))
        content = None
        if not genre:
            genre = choice(ANILIST_GENRES)
            content = f"No genre or tag provided, so I chose random genre: **{genre}**"

        mmap = {
            "anime": ["TV", "TV_SHORT", "MOVIE", "OVA", "ONA", "SPECIAL"],
            "manga": ["MANGA", "NOVEL", "ONE_SHOT"],
        }
        kwargs = {"perPage": 1, "type": media_type.upper(), "format_in": mmap[media_type.lower()]}
        if genre in ANILIST_GENRES:
            results = await MediaData.request(
                ctx.bot.session, query=GENRE_SCHEMA, genre=genre, **kwargs
            )
        else:
            results = await MediaData.request(ctx.bot.session, query=TAG_SCHEMA, tag=genre, **kwargs)

        if isinstance(results, NotFound):
            await ctx.send(
                f"Could not find a random {media_type} from the given genre or tag.",
                ephemeral=True,
            )
            return

        emb = do_media_embed(results[0], await self.to_hide_adult_media(ctx))
        await ctx.send(content=content, embed=emb, ephemeral=True)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    @discord.app_commands.describe(query="Enter the name of the anime/manga character")
    async def character(self, ctx: Context, *, query: str) -> None:
        """Fetch info on a anime/manga character from given query!"""
        await ctx.typing()
        results = await CharacterData.request(
            ctx.bot.session,
            query=CHARACTER_SCHEMA,
            search=query,
            sort="POPULARITY_DESC",
            withRoles=True,
        )
        if isinstance(results, NotFound):
            await ctx.send(str(results), ephemeral=True)
            return

        pages = []
        for idx, page in enumerate(results, start=1):
            emb = do_character_embed(page)
            emb.set_footer(text=f"© anilist.co • Page {idx} of {len(results)}")
            pages.append(emb)
        if len(pages) == 1:
            await ctx.send(embed=pages[0])
            return
        view = WeebView(ctx=ctx, pages=pages, timeout=120)
        view.message = await ctx.send(embed=pages[0], view=view)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    @discord.app_commands.describe(name="Enter the name of the animation studio")
    async def studio(self, ctx: Context, *, name: str) -> None:
        """Fetch info on an animation studio from given name query!"""
        await ctx.typing()
        results = await StudioData.request(ctx.bot.session, query=STUDIO_SCHEMA, search=name)
        if isinstance(results, NotFound):
            await ctx.send(str(results), ephemeral=True)
            return

        pages = []
        for idx, page in enumerate(results, start=1):
            emb = do_studio_embed(page)
            emb.set_footer(text=f"© anilist.co • Page {idx} of {len(results)}")
            pages.append(emb)
        if len(pages) == 1:
            await ctx.send(embed=pages[0])
            return
        view = WeebView(ctx=ctx, pages=pages, timeout=120)
        view.message = await ctx.send(embed=pages[0], view=view)
        return

    @commands.hybrid_command()
    @discord.app_commands.describe(summary_version="Shows the plaintext summary version, easier to read IMO")
    async def upcoming(self, ctx: Context, summary_version: bool = False):
        """Fetch list of upcoming animes airing within a day."""
        await ctx.typing()
        results = await ScheduleData.request(
            ctx.bot.session, query=SCHEDULE_SCHEMA, perPage=20, notYetAired=True, sort="TIME"
        )
        if isinstance(results, NotFound):
            await ctx.send(str(results), ephemeral=True)
            return

        if ctx.interaction:
            embed_links = ctx.interaction.app_permissions.embed_links
        else:
            try:
                embed_links = ctx.channel.permissions_for(ctx.me).embed_links
            except Exception:
                embed_links = discord.Permissions._dm_permissions().embed_links
        if not embed_links or summary_version:
            airing = "\n".join(
                f"<t:{media.airingAt}:R> • {media.media.title}" for media in results
            )
            await ctx.send(
                f"Upcoming animes in next few hours:\n\n{airing}",
                ephemeral=True,
            )
            return

        pages = []
        for idx, page in enumerate(results, start=1):
            emb = do_schedule_embed(page, upcoming=True)
            emb.set_footer(text=f"{emb.footer.text} • Page {idx} of {len(results)}")
            pages.append(emb)
        view = WeebView(ctx=ctx, pages=pages, timeout=120, use_footer=True)
        view.message = await ctx.send(embed=pages[0], view=view)
        return

    @commands.hybrid_command()
    @discord.app_commands.describe(summary_version="Shows the plaintext summary version, easier to read IMO")
    async def lastaired(self, ctx: Context, summary_version: bool = False):
        """Fetch list of upcoming animes airing within a day."""
        await ctx.typing()
        results = await ScheduleData.request(
            ctx.bot.session,
            query=SCHEDULE_SCHEMA,
            perPage=20,
            notYetAired=False,
            sort="TIME_DESC",
        )
        if isinstance(results, NotFound):
            await ctx.send(str(results), ephemeral=True)
            return

        if ctx.interaction:
            embed_links = ctx.interaction.app_permissions.embed_links
        else:
            try:
                embed_links = ctx.channel.permissions_for(ctx.me).embed_links
            except Exception:
                embed_links = discord.Permissions._dm_permissions().embed_links
        if not embed_links or summary_version:
            airing = "\n".join(
                f"<t:{media.airingAt}:R> • {media.media.title}" for media in results
            )
            await ctx.send(
                f"Recently aired animes in past **24 to 48 hours**:\n\n{airing}",
                ephemeral=True,
            )
            return

        pages = []
        for idx, page in enumerate(results, start=1):
            emb = do_schedule_embed(page, upcoming=False)
            emb.set_footer(text=f"{emb.footer.text} • Page {idx} of {len(results)}")
            pages.append(emb)
        view = WeebView(ctx=ctx, pages=pages, timeout=120, use_footer=True)
        view.message = await ctx.send(embed=pages[0], view=view)
        return
        #  await BaseMenu(ListPages(pages), timeout=120, ctx=ctx).start(ctx)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=("mangaka", "seiyuu"))
    @discord.app_commands.describe(name="Enter the name of mangaka, voice actor, anime assistant etc.")
    async def anistaff(self, ctx: Context, *, name: str):
        """Get info on mangaka or anime staff, seiyuu etc."""
        await ctx.typing()
        results = await StaffData.request(ctx.bot.session, query=STAFF_SCHEMA, search=name)
        if isinstance(results, NotFound):
            await ctx.send(str(results), ephemeral=True)
            return

        pages = []
        for idx, page in enumerate(results, start=1):
            emb = do_staff_embed(page)
            emb.set_footer(text=f"© anilist.co • Page {idx} of {len(results)}")
            pages.append(emb)
        if len(pages) == 1:
            await ctx.send(embed=pages[0])
            return
        view = WeebView(ctx=ctx, pages=pages, timeout=120)
        view.message = await ctx.send(embed=pages[0], view=view)
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=["anilistuser"])
    @discord.app_commands.describe(username="The valid username of Anilist user account")
    async def aniuser(self, ctx: Context, username: str):
        """Get info on Anilist user account."""
        await ctx.typing()
        results = await UserData.request(ctx.bot.session, query=USER_SCHEMA, search=username)
        if isinstance(results, NotFound):
            await ctx.send(str(results), ephemeral=True)
            return

        pages = []
        for idx, page in enumerate(results, start=1):
            emb = do_user_embed(page)
            emb.set_footer(text=f"Page {idx} of {len(results)}")
            pages.append(emb)
        if len(pages) == 1:
            await ctx.send(embed=pages[0])
            return
        view = WeebView(ctx=ctx, pages=pages, timeout=120)
        view.message = await ctx.send(embed=pages[0], view=view)
        return

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def anilistset(self, ctx: Context):
        """Group setting command for configuration!"""
        pass

    @anilistset.command()
    async def shownsfw(self, ctx: Context):
        """[For Admins] Setting toggle to show NSFW anime/manga results in this server!"""
        await ctx.typing()
        assert isinstance(ctx.guild, discord.Guild)
        toggle_state: bool = await self.config.guild(ctx.guild).SHOW_ADULT_MEDIA()
        await self.config.guild(ctx.guild).SHOW_ADULT_MEDIA.set(not toggle_state)
        show_or_hide = "**SHOW**" if not toggle_state else "**HIDE**"
        msg = f"I will now {show_or_hide} embed preview for adult animes/mangas in this server!\n"
        if toggle_state:
            msg += "The embed preview for adult animes/manga will only show up in NSFW channels!"
        await ctx.send(msg)
        await ctx.tick()

