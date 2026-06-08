import asyncio
import pandas as pd
import plotly.express as px

from db.supabase_client import get_dataframe
from core.user_segments import filter_users

LEVEL_ORDER = ["débutant", "intermédiaire", "confirmé"]


async def get_spot_distribution_figure(segment: str) -> str:
    df_profiles, df_users, df_spots = await asyncio.gather(
        get_dataframe("user_profiles"),
        get_dataframe("users"),
        get_dataframe("spots"),
    )

    df_profiles = df_profiles[df_profiles["is_active"] == True]

    df_filtered_users = filter_users(df_users, segment)
    df_profiles = df_profiles[df_profiles["user_id"].isin(df_filtered_users["id"])]

    # Explode the favorite_spots UUID array into one row per spot per profile
    df_exploded = df_profiles[["favorite_spots"]].explode("favorite_spots").dropna(subset=["favorite_spots"])
    df_exploded = df_exploded.rename(columns={"favorite_spots": "spot_id"})

    # Join with spots to get names
    spot_names = df_spots[["id", "name"]].rename(columns={"id": "spot_id"})
    df_merged = df_exploded.merge(spot_names, on="spot_id", how="left")
    df_merged["name"] = df_merged["name"].fillna("Unknown")

    df_counts = (
        df_merged.groupby("name")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=True)  # ascending for horizontal bar (top = highest)
    )

    fig = px.bar(
        df_counts,
        x="count",
        y="name",
        orientation="h",
        title=f"Spot Distribution in User Profiles ({segment})",
        labels={"count": "Number of profiles", "name": "Spot"},
        text="count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=max(400, len(df_counts) * 32 + 100),
        margin=dict(l=200, r=60, t=60, b=40),
        yaxis=dict(tickfont=dict(size=12)),
        xaxis=dict(title="Number of profiles"),
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

    df_dist = (
        df_profiles.groupby("spot_count")
        .size()
        .reset_index(name="num_profiles")
    )

    fig = px.bar(
        df_dist,
        x="spot_count",
        y="num_profiles",
        title=f"Number of Spots per Profile ({segment})",
        labels={"spot_count": "Number of spots", "num_profiles": "Number of profiles"},
        text="num_profiles",
    )
    fig.update_traces(textposition="outside")
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

    df = df_profiles[["sport_id", "level"]].dropna(subset=["sport_id", "level"])

    sport_names = df_sports[["id", "display_name"]].rename(columns={"id": "sport_id", "display_name": "sport"})
    df = df.merge(sport_names, on="sport_id", how="left")
    df["sport"] = df["sport"].fillna("Unknown")

    df_counts = df.groupby(["sport", "level"]).size().reset_index(name="count")
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
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=450,
        margin=dict(l=60, r=60, t=60, b=80),
        legend=dict(title="Level"),
    )
    return fig.to_json()
