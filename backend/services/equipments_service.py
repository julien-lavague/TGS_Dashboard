import re
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


UNKNOWN_BRAND = "Non renseignée"
UNMATCHED_BRAND = "Nom libre non reconnu"
DEFAULT_NAME_RE = r"^(kite|wing|foil|board|planche|aile)\s*\d*$"
# Noms courts utilisés au quotidien pour les marques au nom long du catalogue
BRAND_ALIASES = {
    "slingshot": "Slingshot Sports",
    "north": "North Kiteboarding",
    "core": "Core Kiteboarding",
    "armstrong": "Armstrong Foils",
    "axis": "Axis Foils",
    "lift": "Lift Foils",
    "code": "Code Foils",
    "sab": "SAB Foil",
    "ak": "AK Durable Supply Co.",
    "fone": "F-One",
}
BOARD_TYPE_LABELS = {
    "twin-tip": "Twin-tip",
    "surfboard": "Surf",
    "shortboard": "Shortboard",
    "longboard": "Longboard",
    "fish": "Fish",
    "egg": "Egg",
    "gun": "Gun",
    "softboard": "Softboard",
    "malibu": "Malibu",
    "race": "Race",
}


def _brand_resolver(df_products: pd.DataFrame):
    """Déduit la marque d'un équipement : produit du catalogue, puis nom libre."""
    brand_by_product = df_products.set_index("id")["brand"].to_dict()
    brands = sorted(df_products["brand"].dropna().unique(), key=len, reverse=True)
    brand_tokens = {b.lower(): b for b in brands}
    brand_tokens.update({b.lower().split()[0].replace("-", ""): b for b in brands})
    brand_tokens.update(BRAND_ALIASES)

    # Premier mot d'un modèle (« Rebel », « Veloce »…) → marque, s'il n'est pas ambigu
    first_words = (
        df_products.dropna(subset=["product_name", "brand"])
        .assign(word=lambda d: d["product_name"].str.split().str[0].str.lower())
        .groupby("word")["brand"].unique()
    )
    model_tokens = {w: b[0] for w, b in first_words.items() if len(b) == 1 and len(w) >= 3}

    def resolve(name, specs) -> str:
        product_id = specs.get("product_id") if isinstance(specs, dict) else None
        if product_id and product_id in brand_by_product:
            return brand_by_product[product_id]
        text = (name or "").strip().lower()
        if not text or re.match(DEFAULT_NAME_RE, text):
            return UNKNOWN_BRAND
        for token in brands:
            if token.lower() in text:
                return token
        words = re.findall(r"[a-z0-9]+", text.replace("-", ""))
        for w in words:
            if w in brand_tokens:
                return brand_tokens[w]
        for w in words:
            if w in model_tokens:
                return model_tokens[w]
        return UNMATCHED_BRAND

    return resolve


def _stacked_by_level(
    df: pd.DataFrame, color: str, title: str, y_label: str, color_order: list[str], color_map: dict | None = None
) -> str:
    if df.empty:
        fig = px.bar(title=title)
        fig.add_annotation(text="Aucune donnée pour ce segment", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)
        fig.update_layout(height=450, xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig.to_json()

    df_counts = df.groupby(["sport", "level", color]).size().reset_index(name="count")
    totals = df_counts.groupby(["sport", "level"])["count"].transform("sum")
    df_counts["share"] = (df_counts["count"] / totals * 100).round(0)
    df_counts["level"] = pd.Categorical(df_counts["level"], categories=LEVEL_ORDER + ["non renseigné"], ordered=True)
    df_counts = df_counts.sort_values(["sport", "level"])
    df_counts["x_label"] = df_counts["sport"] + " · " + df_counts["level"].astype(str)

    fig = px.bar(
        df_counts,
        x="x_label",
        y="count",
        color=color,
        barmode="stack",
        title=title,
        labels={"count": y_label, "x_label": "", color: ""},
        category_orders={"x_label": df_counts["x_label"].unique().tolist(), color: color_order},
        custom_data=[color, "share"],
        color_discrete_map=color_map or {},
        text="count",
    )
    fig.update_traces(
        textposition="inside",
        hovertemplate="%{x}<br>%{customdata[0]} : %{y} (%{customdata[1]:.0f} %)<extra></extra>",
    )
    fig.update_layout(
        height=450,
        margin=dict(l=60, r=40, t=60, b=80),
        yaxis=dict(title=y_label),
        legend=dict(title=""),
    )
    return fig.to_json()


async def get_equipment_distribution(segment: str) -> dict:
    """Répartition des marques (toutes pièces) et des types de planche, par sport et niveau."""
    df_user_sports, df_equipments, df_users, df_sports, df_products = await asyncio.gather(
        get_dataframe("user_sports"),
        get_dataframe("user_equipments"),
        get_dataframe("users"),
        get_dataframe("sports"),
        get_dataframe("products"),
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
    df["level"] = df["level"].fillna("non renseigné")

    resolve = _brand_resolver(df_products)
    df["brand"] = [resolve(n, s) for n, s in zip(df["name"], df["specs"])]
    # Les pièces au nom par défaut (« Kite 1 »…) sont l'écrasante majorité : on les compte
    # dans le titre mais on ne les empile pas, sinon les marques deviennent illisibles.
    named = df[df["brand"] != UNKNOWN_BRAND]
    known = named.loc[named["brand"] != UNMATCHED_BRAND, "brand"]
    brand_order = known.value_counts().index.tolist() + [UNMATCHED_BRAND]
    n_known = len(known)
    brands_fig = _stacked_by_level(
        named,
        "brand",
        f"Marques des équipements : {n_known} pièce{'s' if n_known > 1 else ''} identifiée{'s' if n_known > 1 else ''}"
        f" sur {len(df)} ({len(df) - len(named)} sans nom ni produit du catalogue, non affichées)",
        "Pièces d'équipement",
        brand_order,
        {UNMATCHED_BRAND: "#d1d5db"},
    )

    boards = df[df["type"] == "board"].copy()
    boards["board_type"] = [
        BOARD_TYPE_LABELS.get(s.get("board_type"), s.get("board_type")) if isinstance(s, dict) and s.get("board_type") else "Non renseigné"
        for s in boards["specs"]
    ]
    board_order = boards["board_type"].value_counts().index.tolist()
    board_types_fig = _stacked_by_level(
        boards,
        "board_type",
        f"Types de planche ({len(boards)} planche{'s' if len(boards) > 1 else ''})",
        "Planches",
        board_order,
    )

    return {"brands": brands_fig, "board_types": board_types_fig}


async def get_equipment_quantity_stats(segment: str) -> dict:
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

    df = df_equipments.merge(
        df_user_sports[["id", "user_id", "sport", "level"]].rename(columns={"id": "user_sport_id"}),
        on="user_sport_id",
        how="inner",
    )

    # Count items per (user, sport, level, type)
    df_counts = (
        df.groupby(["user_id", "sport", "level", "type"])
        .size()
        .reset_index(name="count")
    )

    df_counts["level"] = pd.Categorical(df_counts["level"], categories=LEVEL_ORDER, ordered=True)
    df_counts = df_counts.sort_values(["sport", "level"])

    stats = []
    for (sport, level, eq_type), grp in df_counts.groupby(["sport", "level", "type"], observed=True):
        vals = grp["count"]
        stats.append({
            "sport": sport,
            "level": str(level),
            "type": eq_type,
            "user_count": int(len(vals)),
            "min": int(vals.min()),
            "max": int(vals.max()),
            "mean": round(float(vals.mean()), 2),
            "median": round(float(vals.median()), 2),
        })

    if df_counts.empty:
        fig = px.bar(title="No equipment data")
        fig.update_layout(height=450)
        return {"figure": fig.to_json(), "stats": stats}

    fig = px.box(
        df_counts,
        x="type",
        y="count",
        color="level",
        facet_col="sport",
        points="all",
        title=f"Equipment quantity per user — by sport & level ({segment})",
        labels={"count": "Items per user", "type": "Category", "level": "Level"},
        category_orders={"level": LEVEL_ORDER, "type": list(SPEC_CONFIG.keys())},
    )
    fig.update_traces(boxmean=True)
    fig.update_layout(
        height=450,
        margin=dict(l=60, r=60, t=80, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    return {"figure": fig.to_json(), "stats": stats}


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
