# Attribution: https://github.com/IchBinLeoon/anisearch-discord-bot/blob/main/bot/anisearch/utils/formatters.py
import re
from datetime import datetime
from typing import Mapping, Pattern

import html2text
from redbot.core.utils.chat_formatting import get_number_suffix

HANDLE = html2text.HTML2Text(bodywidth=0)

HTML_TAG_REGEX: Pattern = re.compile(r"\<.*?\>")


def format_birth_date(day: int, month: int | None) -> str:
    if not month:
        return get_number_suffix(day)
    all_months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    return f"{get_number_suffix(day)} {all_months[month - 1]}"


_MEDIA_FORMATS: Mapping[str, str] = {
    # Anime broadcast on television
    "TV": "TV",
    # Anime which are under 15 minutes in length and broadcast on television
    "TV_SHORT": "TV Short",
    # Anime movies with a theatrical release
    "MOVIE": "Movie",
    # Special episodes that have been included in DVD/Blu-ray releases,
    # picture dramas, pilots, etc
    "SPECIAL": "Special Episode",
    # Anime that have been released directly on DVD/Blu-ray without originally
    # going through a theatrical release or television broadcast
    # https://anime.stackexchange.com/q/16728
    "OVA": "OVA",
    # Anime that is originally released online or only available through streaming services.
    # https://anime.stackexchange.com/q/8500
    "ONA": "ONA",
    # Short anime released as a music video
    "MUSIC": "Short Music Video",
    # Professionally published manga with more than one chapter
    "MANGA": "Manga",
    # Written books released as a series of light novel
    "NOVEL": "Light Novel",
    # Manga with just one chapter; often called yomikiri (読み切り)
    "ONE_SHOT": "One-shot Manga",
}


def format_media_type(media_type: str) -> str:
    return _MEDIA_FORMATS.get(media_type, "Unknown")


def format_anime_status(media_status: str) -> str:
    anime_statuses = {
        "FINISHED": "Finished",
        "RELEASING": "Airing",
        "NOT_YET_RELEASED": "Not Yet Aired",
        "CANCELLED": "Cancelled",
        "HIATUS": "On Hiatus",
    }
    return anime_statuses.get(media_status, media_status)


def format_manga_status(media_status: str) -> str:
    manga_statuses = {
        "FINISHED": "Finished",
        "RELEASING": "Publishing",
        "NOT_YET_RELEASED": "Not Yet Published",
        "CANCELLED": "Cancelled",
        "HIATUS": "On Hiatus",
    }
    return manga_statuses.get(media_status, media_status)


def format_description(description: str, length: int = 4086) -> str:
    cleaned = HTML_TAG_REGEX.sub("", description)
    description = cleaned.replace("__", "**").replace("~!", "|| ").replace("!~", " ||")

    if len(description) > length:
        description = description[:length]
        if description.count("||") > 0 and (description.count("|") % 4) != 0:
            return f"{description} || …"
        return f"{description} …"

    return description


def format_date(day: int, month: int, year: int, style: str = 'D') -> str:
    datetime_obj = datetime(year=year, month=month, day=day)
    return f"<t:{int(datetime_obj.timestamp())}:{style}>"

