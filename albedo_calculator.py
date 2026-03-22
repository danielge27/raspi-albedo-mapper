# %%


# %%
# albedo_calculator.py
# Calculates neighborhood-wide albedo score
# and generates specific recommendations

def calculate_neighborhood_albedo(results):
    """
    Weighted average albedo across all detected surfaces
    This is your single most important number
    """
    total_weighted = 0
    total_coverage = 0

    for surface_name, data in results.items():
        weighted = data["coverage_pct"] * data["albedo"]
        total_weighted  += weighted
        total_coverage  += data["coverage_pct"]

    if total_coverage == 0:
        return 0

    avg_albedo = total_weighted / total_coverage
    return round(avg_albedo, 3)


def calculate_heat_index(results):
    """
    Converts albedo score to an easy 0-100 heat risk score
    100 = maximum heat risk
    0   = no heat risk
    """
    albedo = calculate_neighborhood_albedo(results)

    # Lower albedo = higher heat risk
    # Scale: albedo 0.05 → heat 95, albedo 0.65 → heat 35
    heat_index = round((1 - albedo) * 100)
    return heat_index


def get_heat_grade(heat_index):
    """Letter grade + color for the report"""
    if   heat_index >= 85: return "F", "CRITICAL",  "#ff2020"
    elif heat_index >= 70: return "D", "HIGH",       "#ff6600"
    elif heat_index >= 55: return "C", "MODERATE",   "#ffaa00"
    elif heat_index >= 40: return "B", "LOW",        "#88cc00"
    else:                  return "A", "HEALTHY",    "#00dd66"


def generate_recommendations(results, neighborhood_name):
    """
    Generate specific, actionable recommendations
    based on what the image analysis found
    """
    recs = []

    dark    = results.get("dark_roof",     {}).get("coverage_pct", 0)
    asphalt = results.get("asphalt_road",  {}).get("coverage_pct", 0)
    veg     = results.get("vegetation",    {}).get("coverage_pct", 0)
    bright  = results.get("bright_roof",   {}).get("coverage_pct", 0)
    concrete= results.get("concrete",      {}).get("coverage_pct", 0)

    # ── DARK ROOF RECOMMENDATIONS ──────────────────────────
    if dark > 30:
        recs.append({
            "priority": 1,
            "emoji":    "🚨",
            "title":    "Urgent: Green Roof Mandate",
            "detail":   (
                f"{dark:.0f}% of this area has dark tar rooftops — "
                f"the highest heat absorbers in urban environments. "
                f"Mandating white or green roofs on the top 20 "
                f"worst buildings would reduce block temperature "
                f"by an estimated 2–4°F."
            ),
            "policy":   "Recommend: Green Roof Tax Credit Program "
                        "(Boston already has this — expand eligibility)"
        })
    elif dark > 15:
        recs.append({
            "priority": 2,
            "emoji":    "⚠️",
            "title":    "Green Roof Incentive Program",
            "detail":   (
                f"{dark:.0f}% dark rooftops detected. "
                f"A voluntary white-roof incentive program "
                f"targeting these buildings would provide "
                f"meaningful temperature reduction."
            ),
            "policy":   "Recommend: Subsidized cool-roof coating program"
        })

    # ── ASPHALT ROAD RECOMMENDATIONS ───────────────────────
    if asphalt > 20:
        recs.append({
            "priority": 2,
            "emoji":    "🛣️",
            "title":    "Cool Pavement Program",
            "detail":   (
                f"{asphalt:.0f}% asphalt surfaces detected. "
                f"Dark asphalt roads absorb up to 95% of solar "
                f"radiation. Light-colored or reflective pavement "
                f"coatings on major streets could significantly "
                f"reduce the urban heat island effect."
            ),
            "policy":   "Recommend: Pilot light-colored pavement on "
                        "highest-traffic corridors"
        })

    # ── VEGETATION DEFICIT ─────────────────────────────────
    if veg < 15:
        recs.append({
            "priority": 1,
            "emoji":    "🌳",
            "title":    "Critical: Street Tree Planting",
            "detail":   (
                f"Only {veg:.0f}% green vegetation detected — "
                f"well below the 20% minimum for effective "
                f"urban cooling. Each mature street tree provides "
                f"cooling equivalent to 10 room-sized air "
                f"conditioners. This neighborhood needs immediate "
                f"tree canopy investment."
            ),
            "policy":   "Recommend: Emergency street tree planting "
                        "program — target 200 new trees in this zone"
        })
    elif veg < 25:
        recs.append({
            "priority": 3,
            "emoji":    "🌱",
            "title":    "Expand Tree Canopy",
            "detail":   (
                f"{veg:.0f}% vegetation coverage. "
                f"Increasing to 25%+ through parklet creation "
                f"and street tree planting would noticeably "
                f"reduce summer temperatures for residents."
            ),
            "policy":   "Recommend: Prioritize this zone in Boston's "
                        "next urban forestry budget cycle"
        })

    # ── POSITIVE FINDINGS ──────────────────────────────────
    if bright > 20:
        recs.append({
            "priority": 5,
            "emoji":    "✅",
            "title":    "Good: Bright Roof Coverage Present",
            "detail":   (
                f"{bright:.0f}% bright/white roof coverage detected. "
                f"This is a positive sign. These roofs are already "
                f"reflecting significant solar radiation. "
                f"Maintain and expand this practice."
            ),
            "policy":   "Recommend: Feature these buildings in "
                        "cool-roof case study materials"
        })

    # Sort by priority
    recs.sort(key=lambda x: x["priority"])
    return recs


def estimate_temperature_impact(results):
    """
    Rough estimate: how much hotter is this area
    compared to a well-designed urban zone?
    Based on urban heat island research data
    """
    dark    = results.get("dark_roof",   {}).get("coverage_pct", 0)
    asphalt = results.get("asphalt_road",{}).get("coverage_pct", 0)
    veg     = results.get("vegetation",  {}).get("coverage_pct", 0)

    # Each % of dark surface adds ~0.04°F above baseline
    # Each % of vegetation subtracts ~0.03°F
    excess_heat = (dark * 0.04) + (asphalt * 0.03) - (veg * 0.03)
    return round(max(0, excess_heat), 1)

# %%


# %%



