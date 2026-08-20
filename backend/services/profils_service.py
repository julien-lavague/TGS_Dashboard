import asyncio
import json
import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from db.supabase_client import get_dataframe
from core.user_segments import filter_users

LEVEL_ORDER = ["débutant", "intermédiaire", "confirmé"]

# Ordered from offshore to onshore so distributions read logically on the x-axis.
DIRECTION_ORDER = ["offshore", "side-offshore", "side", "side-onshore", "onshore"]

# Compass layout for the orientation radar: offshore at the top (0°), onshore at
# the bottom (180°), the three side orientations mirrored left and right so the
# rose reads like an actual wind window. Each direction is plotted at every angle
# listed here, hence the symmetric shape.
DIRECTION_ANGLES = {
    "offshore":      [0],
    "side-offshore": [45, -45],
    "side":          [90, -90],
    "side-onshore":  [135, -135],
    "onshore":       [180],
}
DIRECTION_SHORT = {
    "side-offshore": "side-off",
    "side-onshore":  "side-on",
}

# Numeric preference parameters stored inside user_profiles.profile_data.
# Each parameter maps to one or more "metrics" (section, field, metric label). A
# parameter with two metrics (e.g. min & max) is drawn as two box series on the
# same chart; the metric label is "" for single-value parameters.
NUMERIC_PARAMS = [
    {"key": "wind_avg",    "label": "Vent moyen",       "unit": "kn", "by_level": True,
     "metrics": [("wind",  "min",        "min"), ("wind",  "max",        "max")]},
    {"key": "gusts",       "label": "Rafales",          "unit": "kn", "by_level": True,
     "metrics": [("wind",  "gusts_min",  "min"), ("wind",  "gusts",      "max")]},
    {"key": "wave_height", "label": "Hauteur de vague", "unit": "m",  "by_level": True,
     "metrics": [("waves", "max_height", "")]},
    {"key": "wave_period", "label": "Période de vague", "unit": "s",
     "metrics": [("waves", "period_min", "min"), ("waves", "period_max", "max")]},
    {"key": "weight",      "label": "Poids du rider",   "unit": "kg",
     "metrics": [(None,    "weight",     "")]},
]

# Categorical direction preferences (a list per profile). `radar` swaps the grouped
# bar chart for one polar chart per sport with a line per level.
DIRECTION_PARAMS = [
    {"key": "wind_directions",  "section": "wind",  "label": "Orientation du vent", "radar": True},
    {"key": "waves_directions", "section": "waves", "label": "Orientation des vagues"},
]

# Toggleable profile modules — whether the user enabled wind / waves / tide.
FEATURE_PARAMS = [
    ("wind",  "Vent"),
    ("waves", "Vague"),
    ("tide",  "Marée"),
]


def _join_emails(series: pd.Series) -> str:
    return "<br>".join(sorted(e for e in series.dropna() if e))


def _as_profile_dict(value):
    """profile_data is JSONB — usually a dict, occasionally a JSON string."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (ValueError, TypeError):
            return {}
    return {}


def _extract_value(profile_data: dict, section, field):
    node = profile_data if section is None else profile_data.get(section)
    if not isinstance(node, dict):
        return None
    return node.get(field)


def _extract_directions(profile_data: dict, section):
    node = profile_data.get(section)
    if not isinstance(node, dict):
        return None
    dirs = node.get("directions")
    return dirs if isinstance(dirs, list) else None


async def get_spot_distribution_figure(segment: str) -> str:
    df_profiles, df_users, df_spots = await asyncio.gather(
        get_dataframe("user_profiles"),
        get_dataframe("users"),
        get_dataframe("spots"),
    )

    df_profiles = df_profiles[df_profiles["is_active"] == True]

    df_filtered_users = filter_users(df_users, segment)
    df_profiles = df_profiles[df_profiles["user_id"].isin(df_filtered_users["id"])]

    email_map = df_filtered_users.set_index("id")["email"].to_dict()

    # Explode the favorite_spots UUID array into one row per spot per profile
    df_exploded = df_profiles[["user_id", "favorite_spots"]].explode("favorite_spots").dropna(subset=["favorite_spots"])
    df_exploded = df_exploded.rename(columns={"favorite_spots": "spot_id"})
    df_exploded["email"] = df_exploded["user_id"].map(email_map)

    # Join with spots to get names
    spot_names = df_spots[["id", "name"]].rename(columns={"id": "spot_id"})
    df_merged = df_exploded.merge(spot_names, on="spot_id", how="left")
    df_merged["name"] = df_merged["name"].fillna("Unknown")

    df_counts = (
        df_merged.groupby("name")
        .agg(count=("email", "count"), emails=("email", _join_emails))
        .reset_index()
        .sort_values("count", ascending=True)
    )

    fig = px.bar(
        df_counts,
        x="count",
        y="name",
        orientation="h",
        title=f"Spot Distribution in User Profiles ({segment})",
        labels={"count": "Number of profiles", "name": "Spot"},
        text="count",
        custom_data=["emails"],
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Count: %{x}<br><br>%{customdata[0]}<extra></extra>",
    )
    fig.update_layout(
        height=max(400, len(df_counts) * 32 + 100),
        margin=dict(l=200, r=60, t=60, b=40),
        yaxis=dict(tickfont=dict(size=12)),
        xaxis=dict(title="Number of profiles"),
    )
    return fig.to_json()


async def get_spot_map_figure(segment: str) -> str:
    """Geographic map of the spots referenced in user profiles, sized/coloured by
    the number of profiles that list each spot as a favorite."""
    df_profiles, df_users, df_spots = await asyncio.gather(
        get_dataframe("user_profiles"),
        get_dataframe("users"),
        get_dataframe("spots"),
    )

    df_profiles = df_profiles[df_profiles["is_active"] == True]
    df_filtered_users = filter_users(df_users, segment)
    df_profiles = df_profiles[df_profiles["user_id"].isin(df_filtered_users["id"])]

    exploded = (
        df_profiles[["user_id", "favorite_spots"]]
        .explode("favorite_spots")
        .dropna(subset=["favorite_spots"])
        .rename(columns={"favorite_spots": "spot_id"})
    )
    counts = exploded.groupby("spot_id").size().reset_index(name="count")

    spots = df_spots[["id", "name", "lat", "lon", "lon2", "region"]].rename(columns={"id": "spot_id"})
    m = counts.merge(spots, on="spot_id", how="left")

    # lon2 is the corrected -180..180 longitude; fall back to normalising lon (0..360).
    m["lon_final"] = pd.to_numeric(m["lon2"], errors="coerce")
    lon = pd.to_numeric(m["lon"], errors="coerce")
    m["lon_final"] = m["lon_final"].fillna(lon.where(lon <= 180, lon - 360))
    m["lat"] = pd.to_numeric(m["lat"], errors="coerce")
    m = m.dropna(subset=["lat", "lon_final"])
    m["name"] = m["name"].fillna("Unknown")
    m["region"] = m["region"].fillna("")

    if m.empty:
        fig = px.scatter_map(lat=[46.6], lon=[2.5], zoom=4)
        fig.update_layout(height=600, margin=dict(l=0, r=0, t=0, b=0),
                          map=dict(style="open-street-map", center=dict(lat=46.6, lon=2.5), zoom=4))
        return fig.to_json()

    center = dict(lat=float(m["lat"].mean()), lon=float(m["lon_final"].mean()))

    fig = px.scatter_map(
        m,
        lat="lat",
        lon="lon_final",
        size="count",
        color="count",
        hover_name="name",
        custom_data=["count", "region"],
        color_continuous_scale="Turbo",
        size_max=28,
        labels={"count": "Profils"},
    )
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]} profil(s)<br>%{customdata[1]}<extra></extra>",
    )
    fig.update_layout(
        height=600,
        margin=dict(l=0, r=0, t=0, b=0),
        map=dict(style="open-street-map", center=center, zoom=4.3),
    )
    return fig.to_json()


def _zoom_for_span(span_deg: float) -> float:
    """Rough MapLibre zoom level to fit a lat/lon span (in degrees)."""
    for limit, zoom in [(0.1, 11), (0.3, 10), (0.6, 9), (1.2, 8), (2.5, 7), (5, 6), (10, 5)]:
        if span_deg <= limit:
            return zoom
    return 4


def _resolve_lonlat(df: pd.DataFrame) -> pd.DataFrame:
    """Add clean numeric `lat` / `lon_final` columns from spots lat/lon/lon2."""
    df = df.copy()
    df["lon_final"] = pd.to_numeric(df["lon2"], errors="coerce")
    lon = pd.to_numeric(df["lon"], errors="coerce")
    df["lon_final"] = df["lon_final"].fillna(lon.where(lon <= 180, lon - 360))
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    return df.dropna(subset=["lat", "lon_final"])


async def get_user_spot_map_figure(segment: str, email: str) -> str:
    """Map of one user's favorite spots (union across their sport profiles) with a
    barycenter marker approximating where the rider is based."""
    df_profiles, df_users, df_spots = await asyncio.gather(
        get_dataframe("user_profiles"),
        get_dataframe("users"),
        get_dataframe("spots"),
    )

    df_profiles = df_profiles[df_profiles["is_active"] == True]
    df_filtered_users = filter_users(df_users, segment)
    user_ids = df_filtered_users[df_filtered_users["email"] == email]["id"].tolist()
    prof = df_profiles[df_profiles["user_id"].isin(user_ids)]

    spot_ids = set()
    for fs in prof["favorite_spots"]:
        if isinstance(fs, list):
            spot_ids.update(s for s in fs if s)

    spots = df_spots[df_spots["id"].isin(spot_ids)][["id", "name", "lat", "lon", "lon2", "region"]]
    spots = _resolve_lonlat(spots)
    spots = spots.assign(name=spots["name"].fillna("Unknown"), region=spots["region"].fillna(""))

    if spots.empty:
        fig = px.scatter_map(lat=[46.6], lon=[2.5], zoom=4)
        fig.update_layout(height=520, margin=dict(l=0, r=0, t=0, b=0),
                          map=dict(style="open-street-map", center=dict(lat=46.6, lon=2.5), zoom=4))
        return fig.to_json()

    bary_lat = float(spots["lat"].mean())
    bary_lon = float(spots["lon_final"].mean())
    span = max(
        float(spots["lat"].max() - spots["lat"].min()),
        float(spots["lon_final"].max() - spots["lon_final"].min()),
        0.02,
    )

    fig = px.scatter_map(
        spots, lat="lat", lon="lon_final", hover_name="name", custom_data=["region"],
    )
    fig.update_traces(
        name="Spots favoris",
        showlegend=True,
        marker=dict(size=12, color="#2563eb"),
        hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]}<extra></extra>",
    )
    fig.add_trace(go.Scattermap(
        lat=[bary_lat], lon=[bary_lon],
        mode="markers+text",
        marker=dict(size=18, color="#dc2626"),
        text=["Localisation présumée"],
        textposition="top center",
        textfont=dict(size=13, color="#dc2626"),
        name="Barycentre",
        hovertemplate="Localisation présumée<br>%{lat:.3f}, %{lon:.3f}<extra></extra>",
    ))
    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=0, b=0),
        map=dict(style="open-street-map", center=dict(lat=bary_lat, lon=bary_lon), zoom=_zoom_for_span(span)),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01,
                    bgcolor="rgba(255,255,255,0.8)"),
    )
    return fig.to_json()


async def get_spots_per_profile_figure(segment: str) -> str:
    df_profiles, df_users = await asyncio.gather(
        get_dataframe("user_profiles"),
        get_dataframe("users"),
    )

    df_profiles = df_profiles[df_profiles["is_active"] == True]
    df_filtered_users = filter_users(df_users, segment)
    df_profiles = df_profiles[df_profiles["user_id"].isin(df_filtered_users["id"])].copy()

    df_profiles["spot_count"] = df_profiles["favorite_spots"].apply(
        lambda x: len(x) if isinstance(x, list) else 0
    )

    email_map = df_filtered_users.set_index("id")["email"].to_dict()
    df_profiles["email"] = df_profiles["user_id"].map(email_map)

    df_dist = (
        df_profiles.groupby("spot_count")
        .agg(num_profiles=("email", "count"), emails=("email", _join_emails))
        .reset_index()
    )

    fig = px.bar(
        df_dist,
        x="spot_count",
        y="num_profiles",
        title=f"Number of Spots per Profile ({segment})",
        labels={"spot_count": "Number of spots", "num_profiles": "Number of profiles"},
        text="num_profiles",
        custom_data=["emails"],
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{x} spot(s)</b><br>Count: %{y}<br><br>%{customdata[0]}<extra></extra>",
    )
    fig.update_layout(
        height=400,
        margin=dict(l=60, r=60, t=60, b=60),
        xaxis=dict(title="Number of spots", dtick=1),
        yaxis=dict(title="Number of profiles"),
    )
    return fig.to_json()


async def get_spots_per_profile_detail(segment: str) -> dict:
    df_profiles, df_users, df_spots = await asyncio.gather(
        get_dataframe("user_profiles"),
        get_dataframe("users"),
        get_dataframe("spots"),
    )

    df_profiles = df_profiles[df_profiles["is_active"] == True]
    df_filtered_users = filter_users(df_users, segment)
    df_profiles = df_profiles[df_profiles["user_id"].isin(df_filtered_users["id"])].copy()

    spot_name_map = df_spots.set_index("id")["name"].to_dict()

    def resolve_spots(ids):
        if not isinstance(ids, list):
            return []
        return [spot_name_map.get(sid, "Unknown") for sid in ids if sid]

    df_profiles["spot_count"] = df_profiles["favorite_spots"].apply(
        lambda x: len(x) if isinstance(x, list) else 0
    )
    df_profiles["spot_names"] = df_profiles["favorite_spots"].apply(resolve_spots)

    email_map = df_filtered_users.set_index("id")["email"].to_dict()
    df_profiles["email"] = df_profiles["user_id"].map(email_map).fillna("unknown")

    users = (
        df_profiles[["email", "spot_count", "spot_names"]]
        .sort_values("spot_count", ascending=False)
        .rename(columns={"spot_names": "spots"})
        .to_dict(orient="records")
    )
    return {"users": users}


async def get_level_by_sport_figure(segment: str) -> str:
    df_profiles, df_users, df_sports = await asyncio.gather(
        get_dataframe("user_profiles"),
        get_dataframe("users"),
        get_dataframe("sports"),
    )

    df_profiles = df_profiles[df_profiles["is_active"] == True]
    df_filtered_users = filter_users(df_users, segment)
    df_profiles = df_profiles[df_profiles["user_id"].isin(df_filtered_users["id"])]

    df = df_profiles[["user_id", "sport_id", "level"]].dropna(subset=["sport_id", "level"])

    sport_names = df_sports[["id", "display_name"]].rename(columns={"id": "sport_id", "display_name": "sport"})
    df = df.merge(sport_names, on="sport_id", how="left")
    df["sport"] = df["sport"].fillna("Unknown")

    email_map = df_filtered_users.set_index("id")["email"].to_dict()
    df["email"] = df["user_id"].map(email_map)

    df_counts = (
        df.groupby(["sport", "level"])
        .agg(count=("email", "count"), emails=("email", _join_emails))
        .reset_index()
    )
    df_counts["level"] = pd.Categorical(df_counts["level"], categories=LEVEL_ORDER, ordered=True)
    df_counts = df_counts.sort_values(["sport", "level"])

    fig = px.bar(
        df_counts,
        x="sport",
        y="count",
        color="level",
        barmode="group",
        title=f"Level Distribution by Sport ({segment})",
        labels={"count": "Number of profiles", "sport": "Sport", "level": "Level"},
        category_orders={"level": LEVEL_ORDER},
        text="count",
        custom_data=["emails"],
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{x}</b> · %{fullData.name}<br>Count: %{y}<br><br>%{customdata[0]}<extra></extra>",
    )
    fig.update_layout(
        height=450,
        margin=dict(l=60, r=60, t=60, b=80),
        legend=dict(title="Level"),
    )
    return fig.to_json()


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def _direction_radar_figure(known, exploded, dirs, sport_order, level_order, label) -> tuple[str, int]:
    """One polar chart per sport, one line per level.

    r = share of that sport+level's profiles (among those that recorded an
    orientation list) having ticked each direction. Returns (figure json, height).
    """
    denom = known.groupby(["sport", "level"], observed=True).size().to_dict()
    num = exploded.groupby(["sport", "level", "dir"], observed=True).size().to_dict()

    sports = [s for s in sport_order if any(denom.get((s, l), 0) for l in level_order)]
    ncols = min(3, len(sports))
    nrows = math.ceil(len(sports) / ncols)
    titles = [f"{s}  (n={sum(denom.get((s, l), 0) for l in level_order)})" for s in sports]

    fig = make_subplots(
        rows=nrows, cols=ncols,
        specs=[[{"type": "polar"}] * ncols for _ in range(nrows)],
        subplot_titles=titles,
        horizontal_spacing=0.08,
        vertical_spacing=0.12,
    )

    palette = px.colors.qualitative.Plotly
    color_of = {lvl: palette[i % len(palette)] for i, lvl in enumerate(level_order)}

    # Ring positions, sorted clockwise from the top (offshore 0° → onshore 180°).
    ring = sorted((a % 360, d) for d, angles in DIRECTION_ANGLES.items() for a in angles)
    theta = [a for a, _ in ring] + [360]        # 360 == 0, closes the polygon
    ring_dirs = [d for _, d in ring] + [ring[0][1]]

    legend_seen: set[str] = set()
    for i, sport in enumerate(sports):
        row, col = divmod(i, ncols)
        for lvl in level_order:
            total = denom.get((sport, lvl), 0)
            if not total:
                continue
            counts = [num.get((sport, lvl, d), 0) for d in ring_dirs]
            pct = [round(c / total * 100, 1) for c in counts]
            color = color_of[lvl]
            fig.add_trace(
                go.Scatterpolar(
                    r=pct,
                    theta=theta,
                    thetaunit="degrees",
                    mode="lines+markers",
                    name=lvl,
                    legendgroup=lvl,
                    showlegend=lvl not in legend_seen,
                    line=dict(color=color, width=2),
                    marker=dict(size=6, color=color),
                    fill="toself",
                    fillcolor=_rgba(color, 0.10),
                    customdata=[[sport, lvl, c, total, d] for c, d in zip(counts, ring_dirs)],
                    hovertemplate=(
                        "<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
                        "%{customdata[4]} : %{r}%<br>"
                        "%{customdata[2]}/%{customdata[3]} profils<extra></extra>"
                    ),
                ),
                row=row + 1, col=col + 1,
            )
            legend_seen.add(lvl)

    fig.update_polars(
        radialaxis=dict(range=[0, 100], ticksuffix=" %", tickfont=dict(size=9), angle=90, dtick=25),
        angularaxis=dict(
            type="linear", period=360, direction="clockwise", rotation=90,
            tickmode="array",
            tickvals=[a for a, _ in ring],
            ticktext=[DIRECTION_SHORT.get(d, d) for _, d in ring],
            tickfont=dict(size=10),
        ),
        bgcolor="rgba(0,0,0,0)",
    )
    for a in fig.layout.annotations:
        a.font.size = 13

    # Anything outside the canonical compass can't be placed on the rose — say so.
    unplaced = [d for d in dirs if d not in DIRECTION_ANGLES]
    subtitle = f"{label} — % de profils ayant coché chaque orientation (rose symétrique gauche/droite)"
    if unplaced:
        subtitle += f" — hors rose : {', '.join(unplaced)}"

    height = nrows * 330 + 90
    fig.update_layout(
        height=height,
        margin=dict(l=50, r=50, t=80, b=40),
        legend=dict(title="Niveau", orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=1),
        title=dict(text=subtitle, x=0, xanchor="left", font=dict(size=12), y=0.99, yanchor="top"),
    )
    return fig.to_json(), height


async def get_profile_characteristics(segment: str, group_by: str = "sport") -> dict:
    """Statistical distributions of profile preferences (wind, gusts, waves, weight,
    orientations) broken down by sport (default) or by favorite spot.

    Mirrors the equipments "characteristics" view: one box plot + stats table per numeric
    parameter, plus grouped bar charts for the categorical orientation preferences.
    In "sport" mode the boxes are grouped by sport and coloured by level; in "spot" mode
    they are grouped (horizontally) by favorite spot and coloured by sport.
    """
    if group_by not in ("sport", "spot"):
        group_by = "sport"

    df_profiles, df_users, df_sports, df_spots = await asyncio.gather(
        get_dataframe("user_profiles"),
        get_dataframe("users"),
        get_dataframe("sports"),
        get_dataframe("spots"),
    )

    df_profiles = df_profiles[df_profiles["is_active"] == True].copy()
    df_filtered_users = filter_users(df_users, segment)
    df_profiles = df_profiles[df_profiles["user_id"].isin(df_filtered_users["id"])].copy()

    sport_names = df_sports[["id", "display_name"]].rename(columns={"id": "sport_id", "display_name": "sport"})
    df_profiles = df_profiles.merge(sport_names, on="sport_id", how="left")
    df_profiles["sport"] = df_profiles["sport"].fillna("Unknown")
    df_profiles["level"] = df_profiles["level"].fillna("inconnu")
    df_profiles["profile_data"] = df_profiles["profile_data"].apply(_as_profile_dict)

    email_map = df_filtered_users.set_index("id")["email"].to_dict()
    df_profiles["email"] = df_profiles["user_id"].map(email_map).fillna("—")

    # Level ordering: known levels first, then anything unexpected.
    present_levels = list(df_profiles["level"].unique())
    level_order = [l for l in LEVEL_ORDER if l in present_levels]
    level_order += sorted(l for l in present_levels if l not in level_order)
    sport_order = sorted(df_profiles["sport"].unique())

    # Build the working frame: a `primary` (box group / x-axis) and a `secondary`
    # (colour) dimension, according to the requested grouping.
    if group_by == "spot":
        spot_name_map = df_spots.set_index("id")["name"].to_dict()
        work = df_profiles.explode("favorite_spots").dropna(subset=["favorite_spots"]).copy()
        work["primary"] = work["favorite_spots"].map(spot_name_map).fillna("Unknown")
        work["secondary"] = work["sport"]
        primary_order = sorted(work["primary"].unique())
        secondary_order = sport_order
        primary_label, secondary_label = "Spot", "Sport"
    else:  # sport
        work = df_profiles
        work["primary"] = work["sport"]
        work["secondary"] = work["level"]
        primary_order = sport_order
        secondary_order = level_order
        primary_label, secondary_label = "Sport", "Niveau"

    figures: dict[str, str] = {}
    stats: list[dict] = []
    params_meta: list[dict] = []

    # --- Numeric parameters -> box plots -------------------------------------
    for p in NUMERIC_PARAMS:
        metrics = p["metrics"]
        multi = len(metrics) > 1
        # Level breakdown only makes sense in sport mode (one facet per level).
        by_level = bool(p.get("by_level")) and group_by == "sport"

        # Melt every metric of this parameter into a single long frame so min & max
        # can be drawn as two box series on the same chart.
        long_frames = []
        for section, field, mlabel in metrics:
            vals = pd.to_numeric(
                work["profile_data"].apply(lambda d, s=section, f=field: _extract_value(d, s, f)),
                errors="coerce",
            )
            long_frames.append(pd.DataFrame({
                "primary": work["primary"].values,
                "secondary": work["secondary"].values,
                "email": work["email"].values,
                "value": vals.values,
                "metric": (mlabel or "valeur"),
            }))
        long = pd.concat(long_frames, ignore_index=True).dropna(subset=["value"])
        if long.empty:
            continue

        metric_order = [m or "valeur" for _, _, m in metrics]

        # Choose colour / facet channels + how the stats table is grouped.
        #   * range parameter (min/max)  -> colour splits min vs max
        #   * by_level                   -> facet one panel per level
        color_col = facet_col = facet_order = None
        color_order = None
        if multi and by_level:
            color_col, color_order = "metric", metric_order
            facet_col, facet_order = "secondary", secondary_order
            stat_group = ["primary", "secondary", "metric"]
            table_secondary_label = f"{secondary_label} · Mesure"
        elif multi:
            color_col, color_order = "metric", metric_order
            stat_group = ["primary", "metric"]
            table_secondary_label = "Mesure"
        elif by_level:
            facet_col, facet_order = "secondary", secondary_order
            stat_group = ["primary", "secondary"]
            table_secondary_label = secondary_label
        else:
            color_col, color_order = "secondary", secondary_order
            stat_group = ["primary", "secondary"]
            table_secondary_label = secondary_label

        params_meta.append({
            "key": p["key"], "label": p["label"], "unit": p["unit"],
            "kind": "numeric", "table_secondary_label": table_secondary_label,
        })

        for keys, g in long.groupby(stat_group, observed=True):
            vals = g["value"].dropna()
            if len(vals) == 0:
                continue
            if len(stat_group) == 3:  # primary, secondary(level), metric
                primary_val, secondary_val = keys[0], f"{keys[1]} · {keys[2]}"
            else:
                primary_val, secondary_val = keys
            stats.append({
                "param": p["key"],
                "unit": p["unit"],
                "primary": str(primary_val),
                "secondary": str(secondary_val),
                "count": int(len(vals)),
                "min": round(float(vals.min()), 2),
                "max": round(float(vals.max()), 2),
                "mean": round(float(vals.mean()), 2),
                "median": round(float(vals.median()), 2),
            })

        axis_label = f'{p["label"]} ({p["unit"]})'
        color_title = "Mesure" if color_col == "metric" else secondary_label
        labels = {"value": axis_label, "primary": primary_label}
        if color_col:
            labels[color_col] = color_title
        if facet_col:
            labels[facet_col] = secondary_label

        cat_orders = {"primary": primary_order}
        if color_col:
            cat_orders[color_col] = color_order
        if facet_col:
            cat_orders[facet_col] = facet_order

        box_kwargs = dict(points="all", custom_data=["email"], labels=labels, category_orders=cat_orders)
        if color_col:
            box_kwargs["color"] = color_col
        if facet_col:
            box_kwargs["facet_col"] = facet_col

        if group_by == "spot":
            fig = px.box(long, x="value", y="primary", orientation="h", **box_kwargs)
            value_ph = "%{x}"
            height = max(400, len(primary_order) * 34 + 140)
        else:
            fig = px.box(long, x="primary", y="value", **box_kwargs)
            value_ph = "%{y}"
            height = 420

        # Show the user's email when hovering an individual point of the distribution.
        fig.update_traces(
            boxmean=True,
            hovertemplate=f'<b>%{{customdata[0]}}</b><br>{p["label"]}: {value_ph} {p["unit"]}<extra></extra>',
        )
        if facet_col:
            fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_layout(
            height=height,
            margin=dict(l=60, r=60, t=60 if facet_col else 40, b=60),
            legend=dict(
                title=(color_title if color_col else None),
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            ),
        )
        figures[p["key"]] = fig.to_json()

    # --- Module activation (wind / waves / tide) by sport & level ------------
    act_frames = []
    for section, flabel in FEATURE_PARAMS:
        enabled = df_profiles["profile_data"].apply(
            lambda d, s=section: bool(_extract_value(d, s, "enabled"))
        )
        act_frames.append(pd.DataFrame({
            "sport": df_profiles["sport"].values,
            "level": df_profiles["level"].values,
            "feature": flabel,
            "enabled": enabled.values,
        }))
    act = pd.concat(act_frames, ignore_index=True)
    act_agg = (
        act.groupby(["sport", "level", "feature"], observed=True)
        .agg(total=("enabled", "size"), active=("enabled", "sum"))
        .reset_index()
    )
    if not act_agg.empty:
        act_agg["pct"] = (act_agg["active"] / act_agg["total"] * 100).round(1)
        params_meta.append({
            "key": "feature_activation",
            "label": "Activation des modules (vent / vague / marée)",
            "unit": "", "kind": "activation",
        })
        fig = px.bar(
            act_agg, x="sport", y="pct", color="feature", barmode="group", facet_col="level",
            text="active",
            labels={"sport": "Sport", "pct": "% de profils activés", "feature": "Module", "level": "Niveau"},
            category_orders={
                "sport": sport_order,
                "level": level_order,
                "feature": [f for _, f in FEATURE_PARAMS],
            },
            custom_data=["active", "total", "level"],
        )
        fig.update_traces(
            textposition="outside",
            hovertemplate="<b>%{fullData.name}</b> · %{x}<br>Activé: %{customdata[0]}/%{customdata[1]} (%{y}%)<extra></extra>",
        )
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_layout(
            height=440,
            margin=dict(l=60, r=60, t=60, b=60),
            yaxis=dict(range=[0, 105], title="% activés"),
            legend=dict(title="Module", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        figures["feature_activation"] = fig.to_json()

    # --- Categorical orientations -> grouped bar charts by sport -------------
    for p in DIRECTION_PARAMS:
        dir_df = df_profiles[["sport", "level"]].copy()
        dir_df["dir"] = df_profiles["profile_data"].apply(lambda d, p=p: _extract_directions(d, p["section"]))
        # Profiles that recorded an orientation list at all — the radar denominator.
        known = dir_df[dir_df["dir"].notna()]
        exploded = known.explode("dir").dropna(subset=["dir"])
        if exploded.empty:
            continue

        present_dirs = [d for d in DIRECTION_ORDER if d in set(exploded["dir"])]
        present_dirs += sorted(d for d in set(exploded["dir"]) if d not in DIRECTION_ORDER)

        if p.get("radar"):
            fig_json, height = _direction_radar_figure(
                known, exploded, present_dirs, sport_order, level_order, p["label"]
            )
            params_meta.append({
                "key": p["key"], "label": p["label"], "unit": "",
                "kind": "radar", "height": height,
            })
            figures[p["key"]] = fig_json
            continue

        params_meta.append({"key": p["key"], "label": p["label"], "unit": "", "kind": "categorical"})

        counts = exploded.groupby(["dir", "sport"], observed=True).size().reset_index(name="count")

        fig = px.bar(
            counts, x="dir", y="count", color="sport", barmode="group", text="count",
            labels={"dir": "Orientation", "count": "Nombre de profils", "sport": "Sport"},
            category_orders={"dir": present_dirs, "sport": sport_order},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            height=400,
            margin=dict(l=60, r=60, t=40, b=60),
            legend=dict(title="Sport", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        figures[p["key"]] = fig.to_json()

    return {
        "group_by": group_by,
        "primary_label": primary_label,
        "secondary_label": secondary_label,
        "params": params_meta,
        "figures": figures,
        "stats": stats,
    }


def _sub_dict(profile_data: dict, key: str) -> dict:
    node = profile_data.get(key)
    return node if isinstance(node, dict) else {}


async def get_user_profiles(segment: str) -> dict:
    """Full per-user profile parameters for the "Fiche utilisateur" tab.

    Returns one entry per user (email) with the list of their sport profiles,
    each carrying the raw wind / waves / tide preferences, weight, favorite spot
    names and equipment.
    """
    df_profiles, df_users, df_sports, df_spots = await asyncio.gather(
        get_dataframe("user_profiles"),
        get_dataframe("users"),
        get_dataframe("sports"),
        get_dataframe("spots"),
    )

    df_profiles = df_profiles[df_profiles["is_active"] == True].copy()
    df_filtered_users = filter_users(df_users, segment)
    df_profiles = df_profiles[df_profiles["user_id"].isin(df_filtered_users["id"])].copy()

    email_map = df_filtered_users.set_index("id")["email"].to_dict()
    sport_map = df_sports.set_index("id")["display_name"].to_dict()
    spot_map = df_spots.set_index("id")["name"].to_dict()
    df_profiles["profile_data"] = df_profiles["profile_data"].apply(_as_profile_dict)

    users: dict[str, list] = {}
    for _, row in df_profiles.iterrows():
        email = email_map.get(row["user_id"], "unknown")
        pdata = row["profile_data"]
        wind, waves, tide = _sub_dict(pdata, "wind"), _sub_dict(pdata, "waves"), _sub_dict(pdata, "tide")

        favorite_spots = row.get("favorite_spots")
        spots = (
            [spot_map.get(sid, "Unknown") for sid in favorite_spots if sid]
            if isinstance(favorite_spots, list) else []
        )

        raw_equipment = pdata.get("equipment")
        equipment = [
            {
                "type": e.get("type"),
                "size": e.get("size"),
                "enabled": bool(e.get("enabled", True)),
            }
            for e in raw_equipment if isinstance(e, dict)
        ] if isinstance(raw_equipment, list) else []

        profile = {
            "sport": sport_map.get(row["sport_id"], "Unknown"),
            "level": row.get("level") or "inconnu",
            "weight": pdata.get("weight"),
            "wind": {
                "enabled": bool(wind.get("enabled", False)),
                "min": wind.get("min"),
                "max": wind.get("max"),
                "gusts_min": wind.get("gusts_min"),
                "gusts": wind.get("gusts"),
                "directions": wind.get("directions") if isinstance(wind.get("directions"), list) else [],
            },
            "waves": {
                "enabled": bool(waves.get("enabled", False)),
                "max_height": waves.get("max_height"),
                "period_min": waves.get("period_min"),
                "period_max": waves.get("period_max"),
                "directions": waves.get("directions") if isinstance(waves.get("directions"), list) else [],
            },
            "tide": {
                "enabled": bool(tide.get("enabled", False)),
                "rising": bool(tide.get("rising", False)),
                "decreasing": bool(tide.get("decreasing", False)),
                "low_tide_avoid": tide.get("low_tide_avoid"),
                "high_tide_avoid": tide.get("high_tide_avoid"),
            },
            "spots": spots,
            "equipment": equipment,
        }
        users.setdefault(email, []).append(profile)

    result = [
        {"email": email, "profiles": sorted(profiles, key=lambda p: p["sport"])}
        for email, profiles in sorted(users.items())
    ]
    return {"users": result}
