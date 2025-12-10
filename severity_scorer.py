# severity_scorer.py
# Threat scoring system with winter hazard integration

class SeverityScorer:
    def __init__(self):
        pass

    def score_alert(self, alert: dict) -> dict:
        """
        Score an alert 0-100 based on type, severity, urgency, and winter hazard factors.
        Expects NWS alert JSON with fields like event, areaDesc, severity, urgency, certainty,
        plus optional winter fields (snowAccumulation, iceAccumulation, windChill).
        """

        base_scores = {
            "Tornado Warning": 90,
            "Severe Thunderstorm Warning": 75,
            "Flash Flood Warning": 70,
            "Winter Storm Warning": 70,
            "Ice Storm Warning": 85,
            "Blizzard Warning": 95,
            "Wind Chill Warning": 65
        }

        event = alert.get("event", "Unknown")
        score = base_scores.get(event, 50)  # default moderate

        # Severity / urgency multipliers
        severity = alert.get("severity", "").lower()
        urgency = alert.get("urgency", "").lower()

        if severity == "extreme":
            score *= 1.15
        elif severity == "severe":
            score *= 1.10

        if urgency == "immediate":
            score *= 1.15
        elif urgency == "expected":
            score *= 1.05

        # Winter hazard factors
        snow = alert.get("snowAccumulation")
        if snow and snow >= 6:  # 6+ inches = dangerous
            score += 10

        ice = alert.get("iceAccumulation")
        if ice and ice >= 0.25:  # 0.25+ inches = crippling ice
            score += 15

        wind_chill = alert.get("windChill")
        if wind_chill is not None and wind_chill <= 0:  # subzero wind chills
            score += 10

        # Cap score at 100
        score = min(round(score), 100)

        # Threat level + color
        if score >= 95:
            level, color, action = "EXTREME", "#FF00FF", "TAKE SHELTER IMMEDIATELY"
        elif score >= 85:
            level, color, action = "SEVERE", "#FF0000", "Take protective action now"
        elif score >= 70:
            level, color, action = "HIGH", "#FF4500", "Be prepared to act quickly"
        elif score >= 50:
            level, color, action = "ELEVATED", "#FFA500", "Stay alert and monitor conditions"
        elif score >= 30:
            level, color, action = "MODERATE", "#FFFF00", "Monitor conditions closely"
        else:
            level, color, action = "LOW", "#00FF00", "Stay aware"

        return {
            "event": event,
            "areaDesc": alert.get("areaDesc", ""),
            "threat_score": score,
            "threat_level": level,
            "color": color,
            "action": action
        }


# ✅ Example usage
if __name__ == "__main__":
    sample_alert = {
        "event": "Winter Storm Warning",
        "areaDesc": "Madison County, AL",
        "severity": "Severe",
        "urgency": "Expected",
        "snowAccumulation": 8,
        "iceAccumulation": 0.3,
        "windChill": -5
    }

    scorer = SeverityScorer()
    scored = scorer.score_alert(sample_alert)
    print(scored)
    # Example output:
    # {
    #   'event': 'Winter Storm Warning',
    #   'areaDesc': 'Madison County, AL',
    #   'threat_score': 100,
    #   'threat_level': 'EXTREME',
    #   'color': '#FF00FF',
    #   'action': 'TAKE SHELTER IMMEDIATELY'
    # }