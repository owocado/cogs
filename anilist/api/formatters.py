# Attribution: https://github.com/IchBinLeoon/anisearch-discord-bot/blob/main/bot/anisearch/utils/formatters.py
import re
from datetime import datetime


def format_media_type(media_type: str) -> str:
    MediaType = {
        'N/A': 'Unknown',
        'TV': 'TV',
        'MOVIE': 'Movie',
        'OVA': 'OVA',
        'ONA': 'ONA',
        'TV_SHORT': 'TV Short',
        'MUSIC': 'Music',
        'SPECIAL': 'Special',
        'ONE_SHOT': 'One Shot',
        'NOVEL': 'Novel',
        'MANGA': 'Manga'
    }
    return MediaType[media_type]


def format_anime_status(media_status: str) -> str:
    AnimeStatus = {
        'FINISHED': 'Finished',
        'RELEASING': 'Currently Airing',
        'NOT_YET_RELEASED': 'Not Yet Aired',
        'CANCELLED': 'Cancelled',
        'None': 'Unknown'
    }
    return AnimeStatus[media_status]


def format_manga_status(media_status: str) -> str:
    MangaStatus = {
        'FINISHED': 'Finished',
        'RELEASING': 'Publishing',
        'NOT_YET_RELEASED': 'Not Yet Published',
        'CANCELLED': 'Cancelled',
        'None': 'Unknown'
    }
    return MangaStatus[media_status]


def clean_html(raw_text) -> str:
    clean = re.compile('<.*?>')
    clean_text = re.sub(clean, '', raw_text)
    return clean_text


def format_description(description: str, length: int) -> str:
    description = clean_html(description)
    description = description.replace('**', '').replace('__', '')
    description = description.replace('~!', '||').replace('!~', '||')
    if len(description) > length:
        description = description[0:length]
        spoiler_tag_count = description.count('||')
        if spoiler_tag_count % 2 != 0:
            return description + '...||'
        return description + '...'
    return description


def format_date(day: int, month: int, year: int) -> str:
    datetime_obj = datetime(year=year, month=month, day=day)
    date = f"<t:{int(datetime_obj.timestamp())}:d>"
    return date