def generate_winter_voice(alert, scored):
    """
    Generate tailored voice announcements for winter hazards.
    Expects alert dict + scored dict (from SeverityScorer).
    """

    event = alert.get("event", "")
    location = alert.get("areaDesc", "")
    score = scored["threat_score"]
    level = scored["threat_level"]

    # Base text
    text = f"{event} for {location}. NorthBamaWX Threat Score: {score} out of 100. Threat level: {level}."

    # Winter-specific tailoring
    if "Winter Storm" in event:
        snow = alert.get("snowAccumulation")
        if snow:
            text += f" Heavy snowfall expected, totals near {snow:.1f} inches. Travel may become impossible."
    if "Ice Storm" in event:
        ice = alert.get("iceAccumulation")
        if ice:
            text += f" Dangerous ice accumulation of {ice:.2f} inches. Power outages and treacherous roads likely."
    if "Blizzard" in event:
        text += " Blizzard conditions possible — near-zero visibility and life-threatening travel hazards."
    if "Wind Chill" in event:
        wc = alert.get("windChill")
        if wc is not None:
            text += f" Wind chills near {wc:.0f}°F. Frostbite risk within minutes of exposure."

    return {
        "text": text,
        "voice_style": scored["threat_level"].lower(),  # maps to calm/concerned/urgent/emergency
        "ssml": f"<speak>{text}</speak>"
    }