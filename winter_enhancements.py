# winter_enhancements.py
# Adds winter weather commentary (snow, ice, wind chill, blizzard conditions)

class WinterEnhancements:
    def __init__(self):
        pass

    def get_winter_story(self, nws_data: dict) -> str | None:
        """
        Generate commentary for winter weather hazards.
        Expects NWS alert/forecast JSON with fields like:
        - snowAccumulation (inches)
        - iceAccumulation (inches)
        - windChill (°F)
        - visibility (miles)
        - windGust (mph)
        """
        story_parts = []

        # Snow accumulation
        snow = nws_data.get("snowAccumulation")
        if snow and snow > 0:
            story_parts.append(
                f"Snowfall totals reaching {snow:.1f} inches in {nws_data.get('location', 'the area')}."
            )

        # Ice accumulation
        ice = nws_data.get("iceAccumulation")
        if ice and ice > 0.1:  # threshold for dangerous ice
            story_parts.append(
                f"Ice accumulation of {ice:.2f} inches expected — hazardous travel conditions likely."
            )

        # Wind chill
        wind_chill = nws_data.get("windChill")
        if wind_chill is not None and wind_chill < 15:  # adjust threshold as needed
            story_parts.append(
                f"Wind chills near {wind_chill:.0f}°F — frostbite risk if exposed."
            )

        # Blizzard / visibility
        visibility = nws_data.get("visibility")
        winds = nws_data.get("windGust")
        if visibility is not None and winds is not None:
            if visibility < 0.25 and winds > 35:
                story_parts.append(
                    "Blizzard conditions possible — near-zero visibility and dangerous winds."
                )

        return " ".join(story_parts) if story_parts else None


# Example usage:
if __name__ == "__main__":
    sample_data = {
        "location": "Madison County, AL",
        "snowAccumulation": 6.2,
        "iceAccumulation": 0.25,
        "windChill": -5,
        "visibility": 0.2,
        "windGust": 40
    }

    winter = WinterEnhancements()
    print(winter.get_winter_story(sample_data))
    # Output:
    # "Snowfall totals reaching 6.2 inches in Madison County, AL.
    #  Ice accumulation of 0.25 inches expected — hazardous travel conditions likely.
    #  Wind chills near -5°F — frostbite risk if exposed.
    #  Blizzard conditions possible — near-zero visibility and dangerous winds."