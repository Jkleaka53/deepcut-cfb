from datetime import datetime, timezone

import pytest
import requests

from cfbm.weather import game_weather

NOW = datetime(2026, 11, 10, 17, tzinfo=timezone.utc)
VENUE = {"latitude": 44.05, "longitude": -123.07, "dome": False}


def never(url, params):
    raise AssertionError("should not call the API")


def hourly(url, params):
    assert "hourly" in params
    return {"hourly": {"time": ["2026-11-14T19:00", "2026-11-14T20:00"],
                       "temperature_2m": [50.0, 52.9], "precipitation_probability": [10, 24],
                       "wind_speed_10m": [6.0, 7.1], "wind_gusts_10m": [12.0, 15.2], "weather_code": [2, 3]}}


def test_dome_is_indoors_without_call():
    assert game_weather({**VENUE, "dome": True}, "2026-11-14T20:30:00.000Z", False, False, NOW, never) == {"status": "indoors"}


def test_far_kickoff_no_call():
    assert game_weather(VENUE, "2026-11-30T20:30:00.000Z", False, False, NOW, never) == {"status": "far"}


def test_completed_is_none():
    assert game_weather(VENUE, "2026-11-08T20:30:00.000Z", False, True, NOW, never) is None


def test_missing_coordinates_is_none():
    assert game_weather({"dome": False}, "2026-11-14T20:30:00.000Z", False, False, NOW, never) is None
    assert game_weather(None, "2026-11-14T20:30:00.000Z", False, False, NOW, never) is None


def test_hourly_forecast_at_kickoff_hour():
    w = game_weather(VENUE, "2026-11-14T20:30:00.000Z", False, False, NOW, hourly)
    assert {k: w[k] for k in ("status", "label", "icon", "tempF", "precipPct", "windMph", "gustMph")} == {
        "status": "forecast", "label": "Cloudy", "icon": "cloudy", "tempF": 53, "precipPct": 24, "windMph": 7,
        "gustMph": 15}
    assert w["asOf"].startswith("2026-11-10T17:00")


def test_tba_uses_daily():
    def daily(url, params):
        assert "daily" in params
        return {"daily": {"time": ["2026-11-14"], "temperature_2m_max": [61.4], "precipitation_probability_max": [70],
                          "wind_speed_10m_max": [18.2], "wind_gusts_10m_max": [30.0], "weather_code": [63]}}
    w = game_weather(VENUE, "2026-11-14T05:00:00.000Z", True, False, NOW, daily)
    assert w["status"] == "tba" and w["tempF"] == 61 and w["icon"] == "rain" and w["precipPct"] == 70


def test_failure_is_none():
    def boom(url, params):
        raise requests.Timeout()
    assert game_weather(VENUE, "2026-11-14T20:30:00.000Z", False, False, NOW, boom) is None


def test_unknown_code():
    def odd(url, params):
        d = hourly(url, params)
        d["hourly"]["weather_code"] = [2, 42]
        return d
    w = game_weather(VENUE, "2026-11-14T20:30:00.000Z", False, False, NOW, odd)
    assert w["label"] == "—" and w["icon"] == "cloudy"


def test_missing_hour_is_none():
    assert game_weather(VENUE, "2026-11-15T20:30:00.000Z", False, False, NOW, hourly) is None
