import asyncio
import numpy as np
import pandas as pd
import plotly.express as px

from db.supabase_client import get_dataframe
from core.user_segments import filter_users

LEVEL_ORDER = ["débutant", "intermédiaire", "confirmé"]

SPEC_CONFIG = {
    "wing":  ("surface",     "m²"),
    "foil":  ("surface",     "cm²"),
    "kite":  ("surface_min", "m²"),
    "board": ("volume",      "L"),
}


async def get_equipment_coverage_figure(segment: str) -> str:
    df_user_sports, df_equipments, df_users, df_sports = await asyncio.gather(
        get_dataframe("user_sports"),
        get_dataframe("user_equipments"),
        get_dataframe("users"),
        get_dataframe("sports"),
    )

    df_user_sports = df_user_sports[df_user_sports["is_active"] == True].copy()
    df_equipments = df_equipments[df_equipments["is_active"] == True]

    df_filtered_users = filter_users(df_users, segment)
    df_user_sports = df_user_sports[df_user_sports["user_id"].isin(df_filtered_users["id"])]

    sport_names = df_sports[["id", "display_name"]].rename(columns={"id": "sport_id", "display_name": "sport"})
    df_user_sports = df_user_sports.merge(sport_names, on="sport_id", how="left")
    df_user_sports["sport"] = df_user_sports["sport"].fillna("Unknown")

    user_sports_with_equip = set(df_equipments["user_sport_id"].unique())
    df_user_sports["has_equipment"] = df_user_sports["id"].isin(user_sports_with_equip)
    df_user_sports["status"] = df_user_sports["has_equipment"].map(
        {True: "With equipment", False: "Without equipment"}
    )

    df_counts = (
        df_user_sports.groupby(["sport", "level", "status"])
        .size()
        .reset_index(name="count")
    )

    df_counts["level"] = pd.Categorical(df_counts["level"], categories=LEVEL_ORDER, ordered=True)
    df_counts = df_counts.sort_values(["sport", "level"])

    df_counts["x_label"] = df_counts["sport"] + " · " + df_counts["level"].astype(str)
    x_order = df_counts["x_label"].unique().tolist()

    fig = px.bar(
        df_counts,
        x="x_label",
        y="count",
        color="status",
        barmode="stack",
        title=f"Equipment Coverage by Sport & Level ({segment})",
        labels={"count": "Users", "x_label": "", "status": ""},
        category_orders={
            "x_label": x_order,
            "status": ["With equipment", "Without equipment"],
        },
        color_discrete_map={
            "With equipment": "#22c55e",
            "Without equipment": "#d1d5db",
        },
        text="count",
    )
    fig.update_traces(textposition="inside", textfont_size=12)
    fig.update_layout(
        height=450,
        margin=dict(l=60, r=60, t=60, b=80),
        yaxis=dict(title="Number of users"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig.to_json()


async def get_equipment_by_type_figure(segment: str) -> str:
    df_user_sports, df_equipments, df_users, df_sports = await asyncio.gather(
        get_dataframe("user_sports"),
        get_dataframe("user_equipments"),
        get_dataframe("users"),
        get_dataframe("sports"),
    )

    df_user_sports = df_user_sports[df_user_sports["is_active"] == True]
    df_equipments = df_equipments[df_equipments["is_active"] == True]

    df_filtered_users = filter_users(df_users, segment)
    df_user_sports = df_user_sports[df_user_sports["user_id"].isin(df_filtered_users["id"])]

    df = df_equipments.merge(
        df_user_sports[["id", "sport_id"]].rename(columns={"id": "user_sport_id"}),
        on="user_sport_id",
        how="inner",
    )

    sport_names = df_sports[["id", "display_name"]].rename(columns={"id": "sport_id", "display_name": "sport"})
    df = df.merge(sport_names, on="sport_id", how="left")
    df["sport"] = df["sport"].fillna("Unknown")

    df_counts = (
        df.groupby(["sport", "type"])
        .size()
        .reset_index(name="count")
        .sort_values(["sport", "count"], ascending=[True, False])
    )

    fig = px.bar(
        df_counts,
        x="type",
        y="count",
        color="sport",
        barmode="group",
        facet_col="sport",
        title=f"Equipment Count by Category & Sport ({segment})",
        labels={"count": "Equipment count", "type": "Category", "sport": "Sport"},
        text="count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=450,
        margin=dict(l=60, r=60, t=80, b=60),
        showlegend=False,
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    return fig.to_json()


async def get_equipment_names(segment: str) -> dict:
    df_user_sports, df_equipments, df_users, df_sports = await asyncio.gather(
        get_dataframe("user_sports"),
        get_dataframe("user_equipments"),
        get_dataframe("users"),
        get_dataframe("sports"),
    )

    df_user_sports = df_user_sports[df_user_sports["is_active"] == True]
    df_equipments = df_equipments[df_equipments["is_active"] == True]

    df_filtered_users = filter_users(df_users, segment)
    df_user_sports = df_user_sports[df_user_sports["user_id"].isin(df_filtered_users["id"])]

    df = df_equipments.merge(
        df_user_sports[["id", "sport_id", "user_id"]].rename(columns={"id": "user_sport_id"}),
        on="user_sport_id",
        how="inner",
    )

    sport_names = df_sports[["id", "display_name"]].rename(columns={"id": "sport_id", "display_name": "sport"})
    df = df.merge(sport_names, on="sport_id", how="left")
    df["sport"] = df["sport"].fillna("Unknown")

    email_map = df_filtered_users.set_index("id")["email"].to_dict()
    df["user"] = df["user_id"].map(email_map).fillna("unknown")

    sports = []
    for sport_name in sorted(df["sport"].unique()):
        sport_df = df[df["sport"] == sport_name]
        categories = []
        for cat_type in sorted(sport_df["type"].unique()):
            items = (
                sport_df[sport_df["type"] == cat_type]
                .sort_values("name")
                [["name", "user"]]
                .fillna("")
                .to_dict(orient="records")
            )
            categories.append({"type": cat_type, "items": items})
        sports.append({"sport": sport_name, "categories": categories})

    return {"sports": sports}


async def get_equipment_characteristics(segment: str) -> dict:
    df_user_sports, df_equipments, df_users, df_sports = await asyncio.gather(
        get_dataframe("user_sports"),
        get_dataframe("user_equipments"),
        get_dataframe("users"),
        get_dataframe("sports"),
    )

    df_user_sports = df_user_sports[df_user_sports["is_active"] == True]
    df_equipments = df_equipments[df_equipments["is_active"] == True]

    df_filtered_users = filter_users(df_users, segment)
    df_user_sports = df_user_sports[df_user_sports["user_id"].isin(df_filtered_users["id"])]

    df = df_equipments.merge(
        df_user_sports[["id", "sport_id", "level"]].rename(columns={"id": "user_sport_id"}),
        on="user_sport_id",
        how="inner",
    )

    sport_names = df_sports[["id", "display_name"]].rename(columns={"id": "sport_id", "display_name": "sport"})
    df = df.merge(sport_names, on="sport_id", how="left")
    df["sport"] = df["sport"].fillna("Unknown")

    stats = []
    figures = {}

    for eq_type, (spec_key, unit) in SPEC_CONFIG.items():
        type_df = df[df["type"] == eq_type].copy()
        type_df["size"] = type_df["specs"].apply(
            lambda s: s.get(spec_key) if isinstance(s, dict) else None
        )
        type_df = type_df.dropna(subset=["size"])
        type_df["size"] = pd.to_numeric(type_df["size"], errors="coerce")
        type_df = type_df.dropna(subset=["size"])

        if type_df.empty:
            continue

        type_df["level"] = pd.Categorical(type_df["level"], categories=LEVEL_ORDER, ordered=True)
        type_df = type_df.sort_values("level")

        for (sport, level), grp in type_df.groupby(["sport", "level"], observed=True):
            vals = grp["size"].dropna()
            if len(vals) == 0:
                continue
            stats.append({
                "sport": sport,
                "level": str(level),
                "type": eq_type,
                "spec": spec_key,
                "unit": unit,
                "count": int(len(vals)),
                "min": round(float(vals.min()), 2),
                "max": round(float(vals.max()), 2),
                "mean": round(float(vals.mean()), 2),
                "median": round(float(vals.median()), 2),
            })

        fig = px.box(
            type_df,
            x="level",
            y="size",
            color="sport",
            points="all",
            title=f"{eq_type.capitalize()} — size distribution ({unit})",
            labels={"size": f"Size ({unit})", "level": "Level", "sport": "Sport"},
            category_orders={"level": LEVEL_ORDER},
        )
        fig.update_traces(boxmean=True)
        fig.update_layout(
            height=400,
            margin=dict(l=60, r=60, t=60, b=60),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        figures[eq_type] = fig.to_json()

    return {"figures": figures, "stats": stats}
