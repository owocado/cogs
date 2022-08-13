import random

from discord import Colour, Embed
from redbot.core.utils.chat_formatting import humanize_number

from .api.character import CharacterData
from .api.formatters import format_birth_date, format_description, format_media_type
from .api.media import MediaData
from .api.schedule import ScheduleData
from .api.studio import StudioData


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

    if data.coverImage.large and data.type == "MANGA":
        embed.set_thumbnail(url=data.coverImage.large)
    embed.set_image(url=data.preview_image)

    if data.type == "ANIME":
        if data.status == "RELEASING":
            if (next_ep := data.nextAiringEpisode) and next_ep.episode:
                next_airing = f" (⏩ Next <t:{next_ep.airingAt}:R>)" if next_ep.airingAt else ""
                description += f"**Episodes:**  {next_ep.episode - 1}{next_airing}\n"
        elif data.episodes:
            description += f"**Episodes:**  {data.episodes}\n"
    elif data.type == "MANGA":
        if data.source:
            description += f"**Source:**  {data.media_source}\n"
        if data.chapters:
            description += f"**Chapters:**  {data.chapters}\n"
        if data.volumes:
            description += f"**Volumes:**  {data.volumes or 0}\n"

    start_date = data.media_start_date
    end_date = data.media_end_date
    if_same_dates = f" to {end_date}" if start_date != end_date else ""
    description += f"**{data.release_mode}**  {start_date}{if_same_dates}\n"

    if data.type == "ANIME":
        if data.duration:
            description += f"**Duration:**  {data.duration} minutes (average)\n"
        description += f"**Source:**  {data.media_source}\n"

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
        f'Episode **{data.episode}** {when} <t:{data.airingAt}:R>\n\n'
        f'**Format:**  {format_media_type(data.media.format)}\n'
    )
    if data.media.duration:
        f'**Duration:** {data.media.duration} minutes (average)'

    if data.media.externalLinks:
        embed.add_field(name="External Links", value=data.external_links)

    air_type = "Upcoming" if upcoming else "Recently Aired"
    embed.set_author(name=f"{air_type} Anime • Episode Info")
    embed.set_thumbnail(url=data.media.coverImage.large or "")
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
