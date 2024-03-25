import random
from collections import OrderedDict
from io import StringIO

#  from arrow.api import get as arrow_get
from discord import Colour, Embed
from redbot.core.utils.chat_formatting import humanize_number, pagify

from .api.character import CharacterData
from .api.formatters import format_birth_date, format_description, format_media_type
from .api.media import MediaData
from .api.schedule import ScheduleData
from .api.staff import Edge as CharacterEdge, StaffData
from .api.studio import StudioData
from .api.user import UserData


def do_character_embed(data: CharacterData) -> Embed:
    emb = Embed(colour=Colour.from_hsv(random.random(), 0.5, 1.0), title=str(data.name))
    emb.description = data.character_summary
    emb.url = data.siteUrl
    emb.set_author(name="Character Info")
    emb.set_thumbnail(url=data.image.large)

    if (dob := data.dateOfBirth) and dob.day and dob.month:
        emb.add_field(name="Birth date:", value=format_birth_date(dob.day, dob.month))
    if synonyms := data.name.alternative:
        emb.add_field(name="Also known as:", value=", ".join(synonyms), inline=False)

    if data.appeared_in:
        emb.add_field(name="Appearances:", value=data.appeared_in, inline=False)
    return emb


def do_media_embed(data: MediaData, hide_adult_media: bool) -> Embed:
    summary = StringIO()
    if data.description:
        summary.write(format_description(data.description, 500))
    summary.write("\n\n")
    embed = Embed(colour=data.prominent_colour, title=str(data.title), url=data.siteUrl)
    # check if result is NSFW and exit early in SFW channel
    if data.isAdult and hide_adult_media:
        embed.colour = 0xFF0000
        embed.description = f"🔞  This {data.type.lower()} is marked as NSFW."
        embed.add_field(
            name="Server admins can opt to show this in SFW channels...",
            value="**by using `;anilistset shownsfw` command!**",
        )
        embed.set_footer(text="Try again in NSFW channel to see full embed!")
        return embed

    # if data.coverImage.large and data.type == "MANGA":
    #     embed.set_thumbnail(url=data.coverImage.large)
    embed.set_image(url=f"https://img.anili.st/media/{data.id}")
    footer_stats = []
    if data.type == "ANIME":
        if data.status == "RELEASING":
            if (next_ep := data.nextAiringEpisode) and next_ep.episode and next_ep.airingAt:
                next_airing = f" • ⏩ Ep {next_ep.episode} <t:{next_ep.airingAt}:R>"
            else:
                next_airing = ""
            summary.write(f"**Episodes:**  {data.episodes}{next_airing}\n")
        elif data.episodes and data.format != "MOVIE":
            footer_stats.append(f"Episode{'s' if data.episodes > 1 else ''}: {data.episodes}")
            summary.write(f"**Episodes:**  {data.episodes}\n")
        if data.duration:
            summary.write(f"**Duration:**  {data.humanize_duration} (average)\n")
    elif data.type == "MANGA":
        if data.chapters:
            footer_stats.append(f"Chapters: {data.chapters}")
            summary.write(f"**Chapters:**  {data.chapters}\n")
        if data.volumes:
            footer_stats.append(f"Volumes: {data.volumes}")
            summary.write(f"**Volumes:**  {data.volumes}\n")
    if data.source:
        summary.write(f"**Source:**  {data.media_source}\n")

    start_date = str(data.startDate)
    end_date = str(data.endDate)
    if_same_dates = f" to {end_date}" if start_date != end_date else ""
    summary.write(f"**{data.release_mode}**  {start_date}{if_same_dates}\n")

    if data.title.native:
        summary.write(f"**Native Title:**  {data.title.native}\n")
    #  if data.synonyms:
        #  embed.add_field(name="Synonyms:", value=data.summarized_synonyms)
    if data.externalLinks:
        embed.add_field(name="External Links:", value=data.external_links, inline=False)

    footer_stats.append(data.media_status)
    if data.format:
        footer_stats.append(f"Type: {format_media_type(data.format)}")
    embed.set_footer(text=" • ".join(footer_stats))
    embed.description = summary.getvalue()
    summary.close()
    return embed


def do_schedule_embed(data: ScheduleData, upcoming: bool) -> Embed:
    embed = Embed(colour=Colour.from_hsv(random.random(), 0.5, 1.0), title=str(data.media.title))
    embed.url = data.media.siteUrl
    when = "airing" if upcoming else "aired"
    footer_stats = []
    summary = StringIO()
    footer_stats.append(f"Episode {data.episode}")
    #  footer_stats.append(f"{when} {arrow_get(data.airingAt).humanize()}")
    summary.write(f"Episode **{data.episode}** {when} <t:{data.airingAt}:R>\n\n")
    media_format = format_media_type(data.media.format)
    footer_stats.append(f"Type: {media_format}")
    summary.write(f"**Format:**  {media_format}\n")
    if data.media.duration:
        footer_stats.append(f"Duration: {data.media.duration} minutes")
        summary.write(f"**Duration:** {data.media.duration} minutes")
    embed.description = summary.getvalue()
    if data.media.externalLinks:
        embed.add_field(name="External Links:", value=data.external_links)
    embed.set_footer(text=" • ".join(footer_stats))
    aired_type = "Upcoming" if upcoming else "Recently Aired"
    embed.set_author(name=f"{aired_type} Anime • Episode Info")
    embed.set_thumbnail(url=data.media.coverImage.large)
    summary.close()
    return embed


def do_staff_embed(data: StaffData) -> Embed:
    embed = Embed(color=Colour.from_hsv(random.random(), 0.5, 1.0), title=str(data.name))
    embed.url = data.siteUrl
    embed.set_thumbnail(url=data.image.large)

    summary = StringIO()
    if date_born := data.dateOfBirth.humanize_date:
        embed.add_field(name="Born:", value=date_born)
        #  summary.write(f"**Birth:**  {data.dateOfBirth}\n")
    if date_died := data.dateOfDeath.humanize_date:
        embed.add_field(name="😨 Died:", value=date_died)
        #  summary.write(f"**Death:**  {data.dateOfDeath}\n")
    if data.age:
        summary.write(f"**Age:**  {data.age} years\n")
    if data.gender:
        summary.write(f"**Gender:**  {data.gender}\n")
    if active := data.yearsActive:
        summary.write(f"**Years active:**  {active[0]}-{data.dateOfDeath.year or 'present'}\n")
    if data.homeTown:
        summary.write(f"**Hometown:**  {data.homeTown}")

    bio_data = StringIO()
    if data.description:
        bio_data.write(format_description(data.description or "", 800))
    if data.description and len(data.description) > len(bio_data.getvalue()):
        bio_data.write(f" [(read more on AniList)]({data.siteUrl})\n")
    embed.description = f"{summary.getvalue()}\n{bio_data.getvalue()}"
    summary.close()
    bio_data.close()

    if jobs := data.primaryOccupations:
        embed.add_field(name="Occupation:", value=", ".join(jobs))
    if pen_names := data.name.alternative:
        if len(pen_names) < 3:
            names = ", ".join(pen_names)
        else:
            names = f"{', '.join(pen_names[:2])} & {len(pen_names) - 2} more"
        embed.add_field(name="Other names:", value=names)

    if data.characterMedia and (edges := data.characterMedia.edges):
        deduped: OrderedDict[str, CharacterEdge] = OrderedDict()
        for e in edges:
            if not e.character:
                continue
            deduped[str(e.character.name)] = e
        characters_list = [
            f"[`{key}`]({v.character.siteUrl}) in {v.node.title}"
            for key, v in deduped.items() if v.character
        ]
        buffer = StringIO()
        buffer.write("\n".join(characters_list))
        for idx, page in enumerate(pagify(buffer.getvalue(), page_length=1024, shorten_by=0), 1):
            embed.add_field(
                name="Popular voiced characters:" if idx == 1 else "\u200b", value=page, inline=False
            )
        buffer.close()
    return embed


def do_studio_embed(data: StudioData) -> Embed:
    emb = Embed(colour=Colour.from_hsv(random.random(), 0.5, 1.0), title=data.name)
    emb.url = data.siteUrl
    popular_works = "\n".join(
        f"{media} ({format_media_type(media.format or '')}){media.episodes_count}"
        for media in data.media.nodes
    )
    emb.description = f"**{len(data.media.nodes)} Most popular productions …**\n\n{popular_works}"
    if data.isAnimationStudio:
        emb.add_field(name="Studio Type:", value="Animation Studio")
    if data.favourites:
        emb.add_field(name="Likes on AniList:", value=humanize_number(data.favourites))
    return emb


def do_user_embed(data: UserData) -> Embed:
    emb = Embed(title=data.name, url=data.siteUrl)
    emb.colour = Colour.from_hsv(random.random(), 0.5, 1.0)
    emb.description = f"account made: {data.created_on}"
    emb.set_image(url=data.opengraph_banner)
    if data.avatar.large:
        emb.set_thumbnail(url=data.avatar.large)
    if data.previousNames:
        emb.add_field(name="Previous Username:", value=data.previous_username)

    if data.statistics.anime.count:
        anime_stats = StringIO()
        anime_stats.write(f"Anime(s) watched: **{data.statistics.anime.count}**\n")
        anime_stats.write(f"Episodes watched: **{data.statistics.anime.episodesWatched}**\n")
        anime_stats.write(
            f"Minutes watched: **{humanize_number(data.statistics.anime.minutesWatched)}**\n"
        )
        if anime_score := data.statistics.anime.meanScore:
            anime_stats.write(f"Mean score: **{anime_score}%**")
        emb.add_field(name="Anime Stats:", value=anime_stats.getvalue(), inline=False)
        anime_stats.close()
    if data.statistics.manga.count:
        manga_stats = StringIO()
        manga_stats.write(f"Manga(s) read: **{data.statistics.manga.count}**\n")
        manga_stats.write(
            f"Chapters read: **{humanize_number(data.statistics.manga.chaptersRead)}**\n"
        )
        if volumes := data.statistics.manga.volumesRead:
            manga_stats.write(f"Volumes read: **{humanize_number(volumes)}**\n")
        if manga_score := data.statistics.manga.meanScore:
            manga_stats.write(f"Mean score: **{manga_score}%**")
        emb.add_field(name="Manga Stats:", value=manga_stats.getvalue(), inline=False)
        manga_stats.close()
    return emb

