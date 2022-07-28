import math
from datetime import datetime


def format_date(date_string: str, style: str = "R", *, prefix: str = "") -> str:
    if not date_string:
        return ""

    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
    # Future proof it in case API changes date string
    except ValueError:
        return ""

    return f"{prefix}<t:{int(date_obj.timestamp())}:{style}>"


# credits to devon
def natural_size(value: int) -> str:
    if value < 1000:
        return str(value)

    units = ('', 'K', 'million', 'billion')
    power = int(math.log(max(abs(value), 1), 1000))
    return f"{value / (1000 ** power):.2f} {units[power]}"