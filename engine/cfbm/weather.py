"""Kickoff weather from Open-Meteo (free, no key, non-commercial with credit)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

import requests

URL = "https://api.open-meteo.com/v1/forecast"
HORIZON = timedelta(days=16)
HOURLY = "temperature_2m,precipitation_probability,wind_speed_10m,wind_gusts_10m,weather_code"
DAILY = "temperature_2m_max,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,weather_code"

CODE_LABELS: dict[int, tuple[str, str]] = {0: ("Clear", "clear"), 1: ("Partly cloudy", "partly-cloudy"),
                                            2: ("Partly cloudy", "partly-cloudy"), 3: ("Cloudy", "cloudy"),
                                            45: ("Fog", "fog"), 48: ("Fog", "fog")}
CODE_LABELS.update({c: ("Drizzle", "drizzle") for c in (51, 53, 55, 56, 57)})
CODE_LABELS.update({c: ("Rain", "rain") for c in (61, 63, 65, 66, 67, 80, 81, 82)})
CODE_LABELS.update({c: ("Snow", "snow") for c in (71, 73, 75, 77, 85, 86)})
CODE_LABELS.update({c: ("Thunderstorms", "storm") for c in (95, 96, 99)})

Fetch = Callable[[str, dict], dict]


def http_fetch(url: str, params: dict) -> dict:
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def _int(v):
    return None if v is None else int(round(float(v)))


def _block(status: str, code, temp, precip, wind, gust, now: datetime) -> dict:
    label, icon = CODE_LABELS.get(_int(code) if code is not None else -1, ("—", "cloudy"))
    return {"status": status, "label": label, "icon": icon, "tempF": _int(temp), "precipPct": _int(precip),
            "windMph": _int(wind), "gustMph": _int(gust), "asOf": now.isoformat()}


def game_weather(venue: dict | None, start_iso: str | None, tbd: bool, completed: bool, now: datetime,
                 fetch_json: Fetch = http_fetch) -> dict | None:
    if completed or not venue:
        return None
    if venue.get("dome"):
        return {"status": "indoors"}
    lat, lon = venue.get("latitude"), venue.get("longitude")
    try:
        kick = datetime.fromisoformat((start_iso or "").replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None
    if lat is None or lon is None:
        return None
    if kick - now > HORIZON:
        return {"status": "far"}
    base = {"latitude": lat, "longitude": lon, "temperature_unit": "fahrenheit", "wind_speed_unit": "mph",
            "timezone": "UTC", "forecast_days": 16}
    try:
        if tbd:
            d = fetch_json(URL, {**base, "daily": DAILY})["daily"]
            i = d["time"].index(kick.strftime("%Y-%m-%d"))
            return _block("tba", d["weather_code"][i], d["temperature_2m_max"][i],
                          d["precipitation_probability_max"][i], d["wind_speed_10m_max"][i],
                          d["wind_gusts_10m_max"][i], now)
        h = fetch_json(URL, {**base, "hourly": HOURLY})["hourly"]
        i = h["time"].index(kick.strftime("%Y-%m-%dT%H:00"))
        return _block("forecast", h["weather_code"][i], h["temperature_2m"][i], h["precipitation_probability"][i],
                      h["wind_speed_10m"][i], h["wind_gusts_10m"][i], now)
    except Exception:  # noqa: BLE001 - any API/shape problem means "no weather", never a failed build
        return None
