from discord import Embed

from .api.media import MediaData
from .api.formatters import format_description, format_media_type

def generate_media_embed(data: MediaData) -> Embed:
    description = format_description(data.description or "", 500) + "\n\n"
    embed = Embed(colour=data.prominent_colour, title=str(data.title), url=data.siteUrl or "")
    if data.coverImage.large and data.type == "MANGA":
        embed.set_thumbnail(url=data.coverImage.large)
    embed.set_image(url=data.preview_image)

    if data.type == "ANIME":
        if data.status == "RELEASING":
            if (next_ep := data.nextAiringEpisode) and next_ep.episode:
                aired_episodes = str(next_ep.episode - 1)
                next_episode_time = ""
                if next_ep.airingAt:
                    next_episode_time = f" (\U000023ef Next <t:{next_ep.airingAt}:R>)"
                description += f"**Episodes:**  {aired_episodes}{next_episode_time}\n"
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
    description += f"**{data.release_mode}**  {start_date} to {end_date}\n"

    if data.type == "ANIME":
        if data.duration:
            description += f"**Duration:**  avg. {data.duration} minutes\n"
        description += f"**Source:**  {data.media_source}\n"

    # if data.synonyms:
    #     embed.add_field(name="Synonyms", value=', '.join(f'`{x}`' for x in data.synonyms))

    sites = []
    if data.trailer and data.trailer.site == "youtube":
        sites.append(f'[Trailer](https://youtu.be/{data.trailer.id})')
    if data.externalLinks:
        for ext_link in data.externalLinks:
            sites.append(str(ext_link))
    if data.idMal:
        sites.append(f'[MyAnimeList](https://myanimelist.net/anime/{data.idMal})')

    if sites:
        embed.add_field(name="External Links", value=" • ".join(sites), inline=False)

    stats = [f'Type: {format_media_type(data.format or "N/A")}', data.media_status]
    embed.set_footer(text=" • ".join(stats))
    embed.description = description
    return embed
