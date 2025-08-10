NAME_TO_ISO = {
    "казахстан": "KZ",
    "россия": "RU",
    "украина": "UA",
    "сша": "US",
    "united states": "US",
    "world": "",  # пустая строка = глобально для pytrends
}


def to_iso(country_name: str) -> str:
    if not country_name:
        return ""
    return NAME_TO_ISO.get(country_name.strip().lower(), "")


