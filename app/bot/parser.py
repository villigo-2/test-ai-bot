from typing import NamedTuple

ALLOWED_TIMEFRAMES = {"7d", "30d", "12m", "5y", "all"}


class ParsedQuery(NamedTuple):
    query: str
    timeframe: str
    country: str  # исходное название
    geo_iso: str  # ISO-код для pytrends


def parse_user_input(text: str) -> ParsedQuery:
    parts = [p.strip() for p in (text or "").split(";")]
    if len(parts) != 3:
        raise ValueError("Ожидаю формат: <термин>; <период>; <страна>")
    query, timeframe, country = parts
    if timeframe not in ALLOWED_TIMEFRAMES:
        raise ValueError("Недопустимый период (7d, 30d, 12m, 5y, all)")
    from app.utils.country_map import to_iso

    geo_iso = to_iso(country)
    return ParsedQuery(query=query, timeframe=timeframe, country=country, geo_iso=geo_iso)


def try_parse_timeframe(text: str) -> str | None:
    tf = (text or "").strip().lower()
    return tf if tf in ALLOWED_TIMEFRAMES else None


