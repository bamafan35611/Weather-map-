
"""
weather_speaker.py - NorthBamaWX Weather Narration Engine

Generates conversational weather text + SSML using:
  • NWS alerts (via LocalPredictor)
  • Threat scores (SeverityScorer)
  • Dynamic voice styles (VoiceStyleManager)
  • National weather snapshots (NWS gridpoints for 5 key cities)

Exposes a single main function:
    build_weather_narration()

This can be called from Flask (e.g. /api/voice/weather-summary)
to drive TTS or other voice output.
"""

import datetime as _dt
import random as _random
from typing import Dict, Any, List, Optional

import requests

# Local modules (already in your project)
from local_predictor import LocalPredictor
from severity_scorer import SeverityScorer
from voice_styles import VoiceStyleManager

# ------------------------------------------------------------------
# National Weather Snapshot (NWS gridpoints)
# ------------------------------------------------------------------

NWS_API_BASE = "https://api.weather.gov"

# 👉 Set this to something that identifies you per NWS guidelines
NWS_USER_AGENT = "NorthBamaWX/1.0 (Weather Narration Engine; contact: you@example.com)"

# 5 key national locations using NWS gridpoints
NATIONAL_GRIDPOINTS = {
    "seattle": {
        "city": "Seattle",
        "region": "Pacific Northwest",
        "office": "SEW",
        "gridX": 124,
        "gridY": 67,
    },
    "denver": {
        "city": "Denver",
        "region": "Rockies",
        "office": "BOU",
        "gridX": 61,
        "gridY": 62,
    },
    "chicago": {
        "city": "Chicago",
        "region": "Midwest",
        "office": "LOT",
        "gridX": 75,
        "gridY": 73,
    },
    "atlanta": {
        "city": "Atlanta",
        "region": "Southeast",
        "office": "FFC",
        "gridX": 52,
        "gridY": 88,
    },
    "nyc": {
        "city": "New York City",
        "region": "Northeast",
        "office": "OKX",
        "gridX": 34,
        "gridY": 35,
    },
}


def _nws_session():
    """Return a requests.Session with NWS headers."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": NWS_USER_AGENT,
            "Accept": "application/geo+json,application/json",
        }
    )
    return session


def _nws_get_forecast_periods(office: str, grid_x: int, grid_y: int, session=None):
    """Fetch forecast periods from NWS gridpoints API for one location."""
    if session is None:
        session = _nws_session()

    url = f"{NWS_API_BASE}/gridpoints/{office}/{grid_x},{grid_y}/forecast"
    try:
        resp = session.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        periods = data.get("properties", {}).get("periods", [])
        if not isinstance(periods, list):
            return []
        return periods
    except Exception as exc:
        print(f"[weather_speaker] Error fetching forecast for {office} {grid_x},{grid_y}: {exc}")
        return []


def _summarize_periods_for_voice(
    periods,
    city: str,
    region: str,
    now: Optional[_dt.datetime] = None,
    rng=None,
) -> Optional[str]:
    """Turn NWS forecast periods into a short, voice-friendly summary."""
    if not periods:
        return None

    if rng is None:
        rng = _random

    # Use first 1–2 periods as a simple short-term snapshot
    p0 = periods[0]
    p1 = periods[1] if len(periods) > 1 else None

    cond0 = (p0.get("shortForecast") or "").strip()
    name0 = (p0.get("name") or "").strip()
    temp0 = p0.get("temperature")
    unit0 = (p0.get("temperatureUnit") or "").upper()

    if not cond0:
        cond_text = "quiet conditions"
    else:
        cond_text = cond0[0].lower() + cond0[1:]

    if region:
        openers = [
            f"In the {region}, {city} is seeing {cond_text}.",
            f"Across the {region}, {city} has {cond_text}.",
            f"{city} in the {region} is dealing with {cond_text}.",
        ]
    else:
        openers = [
            f"{city} is seeing {cond_text}.",
            f"{city} has {cond_text}.",
            f"In {city}, {cond_text} is the story.",
        ]

    line_parts: List[str] = [rng.choice(openers)]

    # Temperature mention
    if temp0 is not None and unit0:
        line_parts[-1] = line_parts[-1].rstrip(".") + f", around {temp0} degrees {unit0}."

    # Second period look-ahead
    if p1 is not None:
        cond1 = (p1.get("shortForecast") or "").strip()
        name1 = (p1.get("name") or "").strip().lower()
        if cond1:
            tail_templates = [
                f"{city} can expect {cond1.lower()} later {name1 or 'on'}.",
                f"Later {name1 or 'on'}, {city} looks for {cond1.lower()}.",
            ]
            line_parts.append(rng.choice(tail_templates))

    sentence = " ".join(line_parts).strip()
    return sentence or None


def build_national_weather_summary(
    now: Optional[_dt.datetime] = None,
    session=None,
    rng=None,
    max_cities: int = 3,
) -> Optional[str]:
    """Build a blended national weather snapshot using a handful of key cities."""
    if rng is None:
        rng = _random
    if now is None:
        now = _dt.datetime.now(_dt.timezone.utc)

    if session is None:
        session = _nws_session()

    city_keys = list(NATIONAL_GRIDPOINTS.keys())
    rng.shuffle(city_keys)  # different mix each time

    summaries: List[str] = []
    for key in city_keys:
        meta = NATIONAL_GRIDPOINTS[key]
        periods = _nws_get_forecast_periods(
            meta["office"],
            meta["gridX"],
            meta["gridY"],
            session=session,
        )
        line = _summarize_periods_for_voice(
            periods,
            city=meta["city"],
            region=meta["region"],
            now=now,
            rng=rng,
        )
        if line:
            summaries.append(line)
        if len(summaries) >= max_cities:
            break

    if not summaries:
        return None

    return " ".join(summaries)


def maybe_get_national_weather_blend(
    alerts_active: bool,
    important_us_event: bool = False,
    now: Optional[_dt.datetime] = None,
    rng=None,
    session=None,
) -> Optional[str]:
    """Smart logic: decide whether to include a national weather section."""
    if rng is None:
        rng = _random
    if now is None:
        now = _dt.datetime.now(_dt.timezone.utc)

    local_now = now.astimezone()
    hour = local_now.hour

    is_peak = (6 <= hour <= 10) or (17 <= hour <= 21)

    if alerts_active:
        include = True
    else:
        if is_peak:
            include = True
        else:
            include = rng.randint(1, 3) == 1  # ~1 in 3 off-peak

    if not include and not important_us_event:
        return None

    core = build_national_weather_summary(now=now, session=session, rng=rng)
    if not core:
        return None

    if alerts_active:
        intro_options = [
            "Elsewhere around the country,",
            "Across the rest of the nation,",
            "Beyond your local area,",
        ]
    else:
        intro_options = [
            "Around the country,",
            "Across the United States,",
            "Looking nationally,",
        ]

    intro = rng.choice(intro_options)
    blended = f"{intro} {core}"

    print(f"[weather_speaker] Using national summary (alerts_active={alerts_active}, peak={is_peak}).")
    return blended


# ------------------------------------------------------------------
# Local alerts + narration helpers
# ------------------------------------------------------------------

def _get_time_of_day_greeting(now: Optional[_dt.datetime] = None) -> str:
    """Return a friendly time-of-day greeting."""
    if now is None:
        now = _dt.datetime.now().astimezone()
    hour = now.hour

    if 5 <= hour < 12:
        return "Good morning from NorthBamaWX."
    if 12 <= hour < 18:
        return "Good afternoon from NorthBamaWX."
    if 18 <= hour < 22:
        return "Good evening from NorthBamaWX."
    return "NorthBamaWX late night update."


def _fetch_scored_alerts() -> List[Dict[str, Any]]:
    """Fetch active NWS alerts and attach threat scores."""
    predictor = LocalPredictor()
    scorer = SeverityScorer()

    alerts_raw = predictor.fetch_active_alerts()
    scored_alerts: List[Dict[str, Any]] = []

    for alert in alerts_raw:
        try:
            ts = scorer.calculate_threat_score(alert)
            alert_with_score = dict(alert)
            alert_with_score["threat_score"] = ts
            scored_alerts.append(alert_with_score)
        except Exception as exc:
            print(f"[weather_speaker] Error scoring alert: {exc}")

    # sort highest threat first
    scored_alerts.sort(key=lambda a: a["threat_score"]["score"], reverse=True)
    return scored_alerts


def _detect_important_us_event(scored_alerts: List[Dict[str, Any]]) -> bool:
    """Return True if something notable is happening nationally."""
    for alert in scored_alerts:
        score = alert["threat_score"]["score"]
        event = (alert.get("event") or "").lower()
        desc = (alert.get("description") or "").lower()

        if score >= 85:
            return True
        if "tornado emergency" in event or "pds" in event or "flash flood emergency" in event:
            return True
        if any(kw in desc for kw in ["tornado emergency", "catastrophic", "unsurvivable"]):
            return True
    return False


def _build_local_alert_narration(scored_alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build narration for the highest-threat alert, plus a brief context line."""
    manager = VoiceStyleManager()

    top = scored_alerts[0]
    threat_score = top["threat_score"]["score"]

    # Use existing alert announcement builder for consistency
    from voice_styles import get_announcement_for_alert  # local import to avoid cycles

    announcement = get_announcement_for_alert(top, threat_score)
    text = announcement["text"]

    # Add quick context about additional alerts if present
    extra = ""
    if len(scored_alerts) > 1:
        extra_count = len(scored_alerts) - 1
        if extra_count == 1:
            extra = " There is also one additional severe weather alert being monitored."
        else:
            extra = f" There are also {extra_count} additional severe weather alerts being monitored across the region."

    full_text = text + extra
    ssml = manager.generate_ssml(full_text, threat_score=threat_score)

    return {
        "text": full_text,
        "ssml": ssml,
        "threat_score": threat_score,
    }


def _build_quiet_weather_narration() -> Dict[str, Any]:
    """Narration used when no severe alerts are active."""
    manager = VoiceStyleManager()
    text = (
        "NorthBamaWX update. There are currently no active severe weather alerts "
        "in the areas we are monitoring. Conditions are generally quiet right now, "
        "but we continue to monitor the atmosphere for any changes."
    )
    # Calm / low threat style
    ssml = manager.generate_ssml(text, threat_score=20)
    return {
        "text": text,
        "ssml": ssml,
        "threat_score": 20,
    }


# ------------------------------------------------------------------
# Main public function
# ------------------------------------------------------------------

def build_weather_narration() -> Dict[str, Any]:
    """Build a complete, blended narration string + SSML."""
    now = _dt.datetime.now(_dt.timezone.utc)

    greeting = _get_time_of_day_greeting(now)

    scored_alerts = _fetch_scored_alerts()
    alerts_active = bool(scored_alerts)

    if alerts_active:
        local_part = _build_local_alert_narration(scored_alerts)
    else:
        local_part = _build_quiet_weather_narration()

    important_us_event = _detect_important_us_event(scored_alerts) if alerts_active else False

    # Try to add national blended commentary
    national_blend = maybe_get_national_weather_blend(
        alerts_active=alerts_active,
        important_us_event=important_us_event,
        now=now,
    )

    speech_parts: List[str] = [greeting, local_part["text"]]
    national_added = False
    if national_blend:
        speech_parts.append(national_blend)
        national_added = True

    final_text = " ".join(part.strip() for part in speech_parts if part).strip()

    # Use top threat score if we have alerts, else the quiet score
    top_threat_score = (
        scored_alerts[0]["threat_score"]["score"] if alerts_active else local_part["threat_score"]
    )

    manager = VoiceStyleManager()
    final_ssml = manager.generate_ssml(final_text, threat_score=top_threat_score)

    return {
        "success": True,
        "text": final_text,
        "ssml": final_ssml,
        "has_alerts": alerts_active,
        "alert_count": len(scored_alerts),
        "top_threat_score": top_threat_score,
        "national_added": national_added,
    }


if __name__ == "__main__":
    # Simple CLI test
    print("=" * 70)
    print("NorthBamaWX Weather Narration Test")
    print("=" * 70)
    result = build_weather_narration()
    print("\nTEXT OUTPUT:")
    print(result["text"])
    print("\nSSML (first 300 chars):")
    print((result["ssml"] or "")[:300] + "...")
    print("\nMeta:", {k: v for k, v in result.items() if k not in ("text", "ssml")})
    print("\nDone.")
