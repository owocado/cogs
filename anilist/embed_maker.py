import random

from discord import Colour, Embed
from redbot.core.utils.chat_formatting import humanize_number

from .api.character import CharacterData
from .api.formatters import format_birth_date, format_description, format_media_type
from .api.media import MediaData
from .api.schedule import ScheduleData
from .api.staff import StaffData
from .api.studio import StudioData
from .api.user import UserData


def do_character_embed(data: CharacterData) -> Embed:
    emb = Embed(colour=Colour.from_hsv(random.random(), 0.5, 1.0), title=str(data.name))
    emb.description = data.character_summary
    emb.url = data.siteUrl or ""
    emb.set_author(name="Character Info")
    emb.set_thumbnail(url=data.image.large or "")

    if (dob := data.dateOfBirth) and dob.day and dob.month:
        emb.add_field(name="Birth Date", value=format_birth_date(dob.day, dob.month))
    if synonyms := data.name.alternative:
        emb.add_field(name="Also known as", value=", ".join(synonyms))

    if data.media_nodes:
        emb.add_field(name="Appearances", value=data.appeared_in, inline=False)
    return emb


def do_media_embed(data: MediaData, is_channel_nsfw: bool) -> Embed:
    description = format_description(data.description or "", 500) + "\n\n"
    embed = Embed(colour=data.prominent_colour, title=str(data.title), url=data.siteUrl or "")

    if data.isAdult and not is_channel_nsfw:
        embed.colour = 0xFF0000
        embed.description = f"This {data.type.lower()} is marked as 🔞 NSFW on AniList."
        embed.set_footer(text="Try again in NSFW channel to see full embed!")
        return embed

    # if data.coverImage.large and data.type == "MANGA":
    #     embed.set_thumbnail(url=data.coverImage.large)
    embed.set_image(url=f"https://img.anili.st/media/{data.id}")

    if data.type == "ANIME":
        if data.status == "RELEASING":
            if (next_ep := data.nextAiringEpisode) and next_ep.episode:
                next_airing = f" (⏩ Next <t:{next_ep.airingAt}:R>)" if next_ep.airingAt else ""
                description += f"**Episodes:**  {next_ep.episode - 1}{next_airing}\n"
        elif data.episodes and data.format != "MOVIE":
            description += f"**Episodes:**  {data.episodes}\n"
        if data.duration:
            description += f"**Duration:**  {data.humanize_duration} (average)\n"
    elif data.type == "MANGA":
        if data.chapters:
            description += f"**Chapters:**  {data.chapters}\n"
        if data.volumes:
            description += f"**Volumes:**  {data.volumes or 0}\n"
    if data.source:
        description += f"**Source:**  {data.media_source}\n"

    start_date = str(data.startDate)
    end_date = str(data.endDate)
    if_same_dates = f" to {end_date}" if start_date != end_date else ""
    description += f"**{data.release_mode}**  {start_date}{if_same_dates}\n"

    # if data.synonyms:
    #     embed.add_field(name="Synonyms", value=', '.join(f'`{x}`' for x in data.synonyms))
    if data.externalLinks:
        embed.add_field(name="External Links", value=data.external_links, inline=False)

    stats = [f'Type: {format_media_type(data.format or "N/A")}', data.media_status]
    embed.set_footer(text=" • ".join(stats))
    embed.description = description
    return embed


def do_schedule_embed(data: ScheduleData, upcoming: bool) -> Embed:
    embed = Embed(colour=Colour.from_hsv(random.random(), 0.5, 1.0), title=str(data.media.title))
    embed.url = data.media.siteUrl
    when = "airing" if upcoming else "aired"
    embed.description = (
        f"Episode **{data.episode}** {when} <t:{data.airingAt}:R>\n\n"
        f"**Format:**  {format_media_type(data.media.format)}\n"
    )
    if data.media.duration:
        f"**Duration:** {data.media.duration} minutes (average)"

    if data.media.externalLinks:
        embed.add_field(name="External Links", value=data.external_links)

    air_type = "Upcoming" if upcoming else "Recently Aired"
    embed.set_author(name=f"{air_type} Anime • Episode Info")
    embed.set_thumbnail(url=data.media.coverImage.large or "")
    return embed


def do_staff_embed(data: StaffData) -> Embed:
    embed = Embed(color=Colour.from_hsv(random.random(), 0.5, 1.0), title=str(data.name))
    embed.url = data.siteUrl or ""
    embed.set_thumbnail(url=data.image.large or "")

    summary = ""
    if data.dateOfBirth.humanize_date:
        summary += f"**Birth:**  {data.dateOfBirth}\n"
    if data.dateOfDeath.humanize_date:
        summary += f"**Death:**  {data.dateOfDeath}\n"
    if data.age:
        summary += f"**Age:**  {data.age} years\n"
    if data.gender:
        summary += f"**Gender:**  {data.gender}\n"
    if active := data.yearsActive:
        summary += f"**Years active:**  {active[0]}-{data.dateOfDeath.year or 'present'}\n"
    if data.homeTown:
        summary += f"**Hometown:**  {data.homeTown}\n"

    bio_data = format_description(data.description or "", 800)
    if data.description and len(data.description) > len(bio_data):
        bio_data += f" [(read more on AniList)]({data.siteUrl})\n"
    embed.description = f"{summary}\n{bio_data}"

    if pen_names := data.name.alternative:
        embed.add_field(name="Other names", value=", ".join(pen_names))
    if jobs := data.primaryOccupations:
        embed.add_field(name="Primary Occupation(s)", value=", ".join(jobs))

    if data.staff_media_nodes:
        staff_roles_list = [
            f"[{media.title}]({media.siteUrl}) ({format_media_type(media.format)})"
            for media in data.staff_media_nodes[:10]
        ]
        notable_staff_roles = ", ".join(staff_roles_list)
        if (total := len(data.staff_media_nodes)) > (parsed := len(staff_roles_list)):
            notable_staff_roles += f" … and {total - parsed} more!"
        embed.add_field(name="Staff / Production Roles", value=notable_staff_roles, inline=False)

    if data.character_nodes:
        character_roles_list = [
            f"[{char.name.full}]({char.siteUrl}) ({char.name.native})"
            for char in data.character_nodes[:10]
        ]
        character_roles = ", ".join(character_roles_list)
        if (total := len(data.character_nodes)) > (parsed := len(character_roles_list)):
            character_roles += f" … and {total - parsed} more!"
        embed.add_field(name="Voiced / Played Characters", value=character_roles, inline=False)
    return embed


def do_studio_embed(data: StudioData) -> Embed:
    emb = Embed(colour=Colour.from_hsv(random.random(), 0.5, 1.0), title=data.name)
    emb.url = data.siteUrl
    popular_works = "\n".join(
        f"{media} ({format_media_type(media.format)}){media.episodes_count}"
        for media in data.media_nodes
    )
    emb.description = f"⏭️  **Most Popular Productions:**\n\n{popular_works}"
    if data.isAnimationStudio:
        emb.add_field(name="Studio Type", value="Animation Studio")
    if data.favourites:
        emb.add_field(name="Likes on AniList", value=humanize_number(data.favourites))
    return emb


def do_user_embed(data: UserData) -> Embed:
    emb = Embed(title=data.name, url=data.siteUrl)
    emb.colour = Colour.from_hsv(random.random(), 0.5, 1.0)
    emb.set_image(url=data.opengraph_banner)
    if data.avatar.large:
        emb.set_thumbnail(url=data.avatar.large)
    if data.previousNames:
        emb.add_field(name="Previous Username", value=data.previous_username)

    if data.statistics.anime.count:
        anime_stats = (
            f"Anime(s) watched: **{data.statistics.anime.count}**\n"
            f"Episodes watched: **{data.statistics.anime.episodesWatched}**\n"
            f"Minutes watched: **{humanize_number(data.statistics.anime.minutesWatched)}**\n"
        )
        if anime_score := data.statistics.anime.meanScore:
            anime_stats += f"Mean score: **{anime_score}%**"
        emb.add_field(name="Anime Stats", value=anime_stats, inline=False)
    if data.statistics.manga.count:
        manga_stats = (
            f"Manga(s) read: **{data.statistics.manga.count}**\n"
            f"Chapters read: **{humanize_number(data.statistics.manga.chaptersRead)}**\n"
        )
        if volumes := data.statistics.manga.volumesRead:
            manga_stats += f"Volumes read: **{humanize_number(volumes)}**\n"
        if manga_score := data.statistics.manga.meanScore:
            manga_stats += f"Mean score: **{manga_score}%**"
        emb.add_field(name="Manga Stats", value=manga_stats, inline=False)

    return emb
