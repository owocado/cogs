# Attribution: https://github.com/IchBinLeoon/anisearch-discord-bot/blob/main/bot/anisearch/utils/formatters.py
import re
from datetime import datetime

import html2text

HANDLE = html2text.HTML2Text(bodywidth=0)


def format_birth_date(day: int, month: int) -> str:
    BirthDate = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    }
    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    value = 'th' if 10 <= (day % 100) <= 20 else suffixes.get(day % 10, 'th')
    return f"{day}{value} {BirthDate.get(month)}"


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
        'NOT_YET_RELEASED': 'Unreleased',
        'CANCELLED': 'Cancelled',
        'None': 'Unknown'
    }
    return AnimeStatus[media_status]


def format_manga_status(media_status: str) -> str:
    MangaStatus = {
        'FINISHED': 'Finished',
        'RELEASING': 'Currently Publishing',
        'NOT_YET_RELEASED': 'Unreleased',
        'CANCELLED': 'Cancelled',
        'None': 'Unknown'
    }
    return MangaStatus[media_status]


def clean_html(raw_text) -> str:
    clean = re.compile('<.*?>')
    clean_text = re.sub(clean, '', raw_text)
    return clean_text


def format_description(description: str, length: int) -> str:
    cleaned = clean_html(description)
    description = cleaned.replace('__', '**').replace('~!', '|| ').replace('!~', ' ||')

    if len(description) > length:
        description = description[:length]
        if (description.count('|') % 4) != 0:
            return description + ' || …'
        return description + ' …'

    return description


def format_date(day: int, month: int, year: int) -> str:
    datetime_obj = datetime(year=year, month=month, day=day)
    date = f"<t:{int(datetime_obj.timestamp())}:D>"
    return date
