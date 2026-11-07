"""Usage des widgets de la page /sessions, à partir de la table ui_events.

ui_events est alimentée par l'app (trackUiEvent) : un événement par
interaction, plus un résumé de la profondeur de timeline par visite et une vue
par CTA Premium affiché. Contrairement à user_analytics dans usage_service,
les visiteurs anonymes sont gardés : ils sont la majorité de ceux qui voient
les incitations Premium.
"""
import asyncio
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from db.supabase_client import get_dataframe
from core.user_segments import filter_users


DEV_ORIGINS = ("https://dev.thegoodspots.fr/", "http://localhost", "http://127.0.0.1")

# Événements qui traduisent une action de l'utilisateur. Les vues de CTA,
# l'affichage de la visite guidée et le résumé de scroll partent sans geste.
INTERACTION_EVENTS = {
    "click", "open", "change", "search", "use", "trigger", "submit", "share", "paywall_click",
}

# Tous les éléments suivis sur /sessions, par famille : un élément jamais
# touché doit apparaître à 0 % et non disparaître du graphique.
ELEMENT_GROUPS = {
    "Timeline": [
        "timeline_cell", "timeline_spot_label", "timeline_spot_menu", "timeline_wind_edit",
        "timeline_scrubber", "timeline_keyboard", "timeline_drag", "slot_timeline",
    ],
    "Filtres": [
        "display_metric", "score_filter", "wind_filter", "view_mode",
        "sport_switcher", "profile_edit", "satellite_toggle",
    ],
    "Bulles": ["bubble_spots", "bubble_community", "bubble_live", "menu"],
    "Carte": [
        "map_spot", "map_neighbor_spot", "map_add_favorite", "map_live_count",
        "map_wind_edit", "map_poi", "map_zone", "map_zoom_out_to_all",
        "map_relief3d", "map_depth", "map_tide_tab",
    ],
    "Modales": ["wind_sectors_editor", "live_report", "live_spot_detail", "tour", "guest_auth_prompt", "error_retry"],
    "Premium": [
        "cta_arome_pi", "cta_timeline_column", "cta_timeline_banner", "cta_multisport",
        "cta_spot_limit", "cta_locked_badge", "cta_teaser_marker", "cta_slot_timeline",
    ],
}
# Éléments renommés quand le widget a changé de place : l'historique suit le nouveau nom.
# La bulle Relief 3D est devenue le bouton « Mon Spot en 3D » du widget Carte/Satellite.
ELEMENT_ALIASES = {"bubble_relief3d": "map_relief3d"}

# Éléments propres à un format d'écran : 0 % sur l'autre n'est pas un désintérêt.
ONLY_ON = {"bubble_spots": "desktop", "map_tide_tab": "mobile"}
VIEWPORT_LABELS = {"mobile": "Téléphone", "desktop": "Grand écran"}
MOBILE_UA = r"Mobi|Android|iPhone|iPod"

GROUP_OF = {el: group for group, els in ELEMENT_GROUPS.items() for el in els}
PAYWALL_ELEMENTS = ELEMENT_GROUPS["Premium"]
TIER_ORDER = ["visiting", "signed_in", "early_adopter", "premium"]


def _empty_figure(message: str) -> str:
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(size=14))
    fig.update_layout(xaxis_visible=False, yaxis_visible=False, template="plotly_white")
    return fig.to_json()


def _filter_dev(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "page_url" not in df.columns:
        return df
    return df[~df["page_url"].fillna("").str.startswith(DEV_ORIGINS)]


def _filter_days(df: pd.DataFrame, column: str, days: Optional[int]) -> pd.DataFrame:
    if df.empty or days is None:
        return df
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days)
    return df[pd.to_datetime(df[column], format="mixed", utc=True) >= cutoff]


def _filter_segment(df: pd.DataFrame, df_users: pd.DataFrame, segment: str) -> pd.DataFrame:
    """Utilisateurs du segment, plus les visiteurs anonymes pour release et all."""
    if df.empty:
        return df
    allowed = set(filter_users(df_users, segment)["id"])
    in_segment = df["user_id"].isin(allowed)
    if segment in ("release", "all"):
        return df[in_segment | df["user_id"].isna()]
    return df[in_segment]


async def _load(segment: str, days: Optional[int]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(ui_events de /sessions, visites de /sessions, user_analytics brut)."""
    df_events, df_analytics, df_users = await asyncio.gather(
        get_dataframe("ui_events"),
        get_dataframe("user_analytics"),
        get_dataframe("users"),
    )
    df_visits = df_analytics
    if not df_events.empty:
        df_events = df_events[df_events["page_type"] == "sessions"]
        df_events = _filter_segment(_filter_days(_filter_dev(df_events), "created_at", days), df_users, segment).copy()
        df_events["props"] = df_events["props"].apply(lambda p: p if isinstance(p, dict) else {})
        df_events["element"] = df_events["element"].replace(ELEMENT_ALIASES)
        # Écran posé par l'app sur chaque événement ; les plus anciens n'en ont pas
        df_events["viewport"] = df_events["props"].apply(lambda p: p.get("viewport") or "unknown")
        df_events["tier"] = df_events["tier"].fillna("unknown")
    if not df_visits.empty:
        df_visits = df_visits[df_visits["page_type"] == "sessions"]
        df_visits = _filter_segment(_filter_days(_filter_dev(df_visits), "entry_time", days), df_users, segment).copy()
        is_mobile = df_visits["user_agent"].fillna("").str.contains(MOBILE_UA, regex=True)
        df_visits["viewport"] = is_mobile.map({True: "mobile", False: "desktop"})
    return df_events, df_visits, df_analytics


def _prop(df: pd.DataFrame, key: str) -> pd.Series:
    return df["props"].apply(lambda p: p.get(key))


async def get_element_usage_figure(segment: str, days: Optional[int] = None) -> str:
    """Part des visites de /sessions où chaque élément a été utilisé au moins une fois,
    sur téléphone et sur grand écran : la page n'y montre pas les mêmes widgets."""
    df_events, df_visits, _ = await _load(segment, days)
    if df_events.empty:
        return _empty_figure("Aucun événement ui_events sur la période")

    used = df_events[df_events["event"].isin(INTERACTION_EVENTS)]
    rows = []
    totals = {}
    for vp in ("mobile", "desktop"):
        visits_vp = df_visits[df_visits["viewport"] == vp] if not df_visits.empty else df_visits
        n_visits = max(visits_vp["session_id"].nunique() if not visits_vp.empty else 0,
                       df_events.loc[df_events["viewport"] == vp, "session_id"].nunique())
        totals[vp] = n_visits
        by_element = used[used["viewport"] == vp].groupby("element")["session_id"].nunique()
        elements = list(GROUP_OF) + [e for e in used["element"].unique() if e not in GROUP_OF]
        for e in elements:
            if ONLY_ON.get(e, vp) != vp:
                continue
            n = int(by_element.get(e, 0))
            rows.append({
                "écran": VIEWPORT_LABELS[vp],
                "element": e,
                "groupe": GROUP_OF.get(e, "Autre"),
                "visites": n,
                "part": round(n / n_visits * 100, 1) if n_visits else 0.0,
            })
    df = pd.DataFrame(rows)

    # Même ordre dans les deux colonnes : par part moyenne
    order = df.groupby("element")["part"].mean().sort_values().index.tolist()
    fig = px.bar(
        df, x="part", y="element", color="groupe", orientation="h", facet_col="écran",
        category_orders={"écran": list(VIEWPORT_LABELS.values()), "element": order[::-1]},
        text=df["part"].map(lambda v: f"{v:g} %"),
        hover_data={"visites": True, "part": ":.1f"},
        labels={"part": "% des visites", "element": ""},
        template="plotly_white",
    )
    fig.for_each_annotation(lambda a: a.update(text=(
        f"{a.text.split('=')[-1]} — {totals['mobile' if 'Téléphone' in a.text else 'desktop']} visites"
    )))
    fig.update_layout(
        title="Visites de /sessions — un élément à 0 % n'a jamais été utilisé (absent si l'écran ne l'affiche pas)",
        legend_title_text="",
        height=max(500, 22 * len(order)),
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return fig.to_json()


async def get_timeline_depth_figure(segment: str, days: Optional[int] = None) -> str:
    """Jusqu'où la timeline est parcourue, par tier, et part qui franchit l'horizon 24 h."""
    df_events, _, _ = await _load(segment, days)
    df = df_events[(df_events["event"] == "scroll_summary") & (df_events["element"] == "timeline")] if not df_events.empty else df_events
    if df.empty:
        return _empty_figure("Aucun résumé de timeline sur la période")

    df = df.assign(
        max_hours_ahead=_prop(df, "max_hours_ahead").astype(float),
        crossed_lock=_prop(df, "crossed_lock").fillna(False).astype(bool),
        has_lock=_prop(df, "has_lock").fillna(False).astype(bool),
        nav=_prop(df, "nav").fillna("none"),
    )
    tiers = [t for t in TIER_ORDER if t in df["tier"].unique()] + [t for t in df["tier"].unique() if t not in TIER_ORDER]

    fig = make_subplots(
        rows=1, cols=3, column_widths=[0.55, 0.2, 0.25],
        subplot_titles=("Heures d'avance atteintes (max par visite)", "Franchit l'horizon 24 h", "Moyens de navigation"),
    )
    for tier in tiers:
        sub = df[df["tier"] == tier]
        fig.add_trace(go.Histogram(x=sub["max_hours_ahead"], name=tier, xbins=dict(size=6), opacity=0.75), row=1, col=1)

    locked = df[df["has_lock"]]
    if not locked.empty:
        share = locked.groupby("tier")["crossed_lock"].mean().mul(100).round(1)
        fig.add_trace(go.Bar(x=share.index, y=share.values, text=share.map(lambda v: f"{v:g} %"),
                             showlegend=False, marker_color="#0ea5e9"), row=1, col=2)

    nav = df["nav"].str.split(",").explode()
    nav_share = (nav.value_counts() / len(df) * 100).round(1)
    fig.add_trace(go.Bar(x=nav_share.index, y=nav_share.values, text=nav_share.map(lambda v: f"{v:g} %"),
                         showlegend=False, marker_color="#14b8a6"), row=1, col=3)

    fig.update_layout(barmode="overlay", template="plotly_white", legend_title_text="tier",
                      title=f"{len(df)} visites — médiane {df['max_hours_ahead'].median():g} h d'avance")
    fig.update_xaxes(title_text="heures après maintenant", row=1, col=1)
    fig.update_yaxes(title_text="visites", row=1, col=1)
    fig.update_yaxes(title_text="% des visites limitées", row=1, col=2)
    fig.update_yaxes(title_text="% des visites", row=1, col=3)
    return fig.to_json()


async def get_cell_clicks_figure(segment: str, days: Optional[int] = None) -> str:
    """Clics sur les scores individuels : à quelle échéance, sur quel score, quel rang de spot."""
    df_events, _, _ = await _load(segment, days)
    df = df_events[(df_events["element"] == "timeline_cell") & (df_events["event"] == "click")] if not df_events.empty else df_events
    if df.empty:
        return _empty_figure("Aucun clic sur une cellule de timeline sur la période")

    df = df.assign(
        hours_ahead=_prop(df, "hours_ahead").astype(float),
        score=pd.to_numeric(_prop(df, "score"), errors="coerce"),
        spot_rank=pd.to_numeric(_prop(df, "spot_rank"), errors="coerce"),
        locked=_prop(df, "locked").fillna(False).astype(bool),
    )
    fig = make_subplots(rows=1, cols=3, subplot_titles=("Échéance cliquée", "Score cliqué", "Rang du spot (0 = en haut)"))
    for locked, color, name in ((False, "#22c55e", "score visible"), (True, "#94a3b8", "verrouillé")):
        sub = df[df["locked"] == locked]
        fig.add_trace(go.Histogram(x=sub["hours_ahead"], xbins=dict(size=3), name=name, marker_color=color), row=1, col=1)
    fig.add_trace(go.Histogram(x=df["score"].dropna(), xbins=dict(start=0, end=100, size=10),
                               showlegend=False, marker_color="#0ea5e9"), row=1, col=2)
    ranks = df["spot_rank"].dropna().astype(int).value_counts().sort_index()
    fig.add_trace(go.Bar(x=ranks.index, y=ranks.values, showlegend=False, marker_color="#14b8a6"), row=1, col=3)

    fig.update_layout(barmode="stack", template="plotly_white",
                      title=f"{len(df)} clics sur {df['session_id'].nunique()} visites")
    fig.update_xaxes(title_text="heures après maintenant", row=1, col=1)
    fig.update_xaxes(title_text="score /100", row=1, col=2)
    return fig.to_json()


async def get_filters_figure(segment: str, days: Optional[int] = None) -> str:
    """Seuils de score choisis, et bascules de mode de vue."""
    df_events, _, _ = await _load(segment, days)
    if df_events.empty:
        return _empty_figure("Aucun événement sur la période")
    n_visits = df_events["session_id"].nunique()
    thr = df_events[(df_events["element"] == "score_filter") & (df_events["event"] == "change")]
    vm = df_events[(df_events["element"] == "view_mode") & (df_events["event"] == "change")]

    fig = make_subplots(rows=1, cols=2, subplot_titles=(
        f"Seuil de score choisi — {thr['session_id'].nunique()} visites sur {n_visits}",
        f"Mode de vue atteint — {vm['session_id'].nunique()} visites sur {n_visits}",
    ))
    if not thr.empty:
        to = pd.to_numeric(_prop(thr, "to"), errors="coerce").dropna().astype(int).value_counts().sort_index()
        fig.add_trace(go.Bar(x=to.index.astype(str), y=to.values, showlegend=False, marker_color="#0ea5e9"), row=1, col=1)
    if not vm.empty:
        vm = vm.assign(to=_prop(vm, "to"), trigger=_prop(vm, "trigger"))
        counts = vm.groupby(["to", "trigger"]).size().reset_index(name="n")
        for trigger in counts["trigger"].unique():
            sub = counts[counts["trigger"] == trigger]
            fig.add_trace(go.Bar(x=sub["to"], y=sub["n"], name=f"via {trigger}"), row=1, col=2)
    fig.update_layout(barmode="stack", template="plotly_white")
    fig.update_xaxes(title_text="score minimum", row=1, col=1)
    fig.update_yaxes(title_text="changements", row=1, col=1)
    return fig.to_json()


async def get_paywall_funnel_figure(segment: str, days: Optional[int] = None) -> str:
    """Entonnoir par CTA Premium : vue → clic → page pricing → abonnement."""
    (df_events, _, df_pricing), df_subs = await asyncio.gather(
        _load(segment, days),
        get_dataframe("subscriptions"),
    )
    if df_events.empty:
        return _empty_figure("Aucun événement sur la période")

    views = df_events[df_events["event"] == "paywall_view"]
    clicks = df_events[df_events["event"] == "paywall_click"]
    pricing_sessions = set(df_pricing.loc[df_pricing["page_type"] == "pricing", "session_id"]) if not df_pricing.empty else set()

    premium_since: dict = {}
    if not df_subs.empty:
        paid = df_subs[df_subs["status"].isin(["active", "trialing", "past_due"]) & (df_subs["plan"] == "premium")]
        premium_since = dict(zip(paid["user_id"], pd.to_datetime(paid["created_at"], format="mixed", utc=True)))

    rows = []
    for element in PAYWALL_ELEMENTS:
        v = views[views["element"] == element]
        c = clicks[clicks["element"] == element]
        c_users = c.dropna(subset=["user_id"])
        converted = sum(
            1 for uid, grp in c_users.groupby("user_id")
            if uid in premium_since and premium_since[uid] >= pd.to_datetime(grp["created_at"], format="mixed", utc=True).min()
        )
        rows.append({
            "cta": element,
            "vues (visites)": v["session_id"].nunique(),
            "clics (visites)": c["session_id"].nunique(),
            "→ pricing": len(set(c["session_id"]) & pricing_sessions),
            "→ premium": converted,
        })
    df = pd.DataFrame(rows)
    df["taux de clic"] = (df["clics (visites)"] / df["vues (visites)"].where(df["vues (visites)"] > 0)).mul(100).round(1)

    # Clics par tier, pour voir qui répond à chaque incitation
    by_tier = clicks.groupby(["element", "tier"])["session_id"].nunique().reset_index(name="n")

    fig = make_subplots(
        rows=2, cols=1, row_heights=[0.55, 0.45], vertical_spacing=0.12,
        specs=[[{"type": "table"}], [{"type": "xy"}]],
        subplot_titles=("Entonnoir par CTA (visites distinctes)", "Clics par tier"),
    )
    fig.add_trace(go.Table(
        header=dict(values=list(df.columns), fill_color="#0ea5e9", font=dict(color="white"), align="left"),
        cells=dict(values=[df[c].fillna("—") for c in df.columns], align="left"),
    ), row=1, col=1)
    for tier in [t for t in TIER_ORDER if t in by_tier["tier"].unique()]:
        sub = by_tier[by_tier["tier"] == tier]
        fig.add_trace(go.Bar(x=sub["element"], y=sub["n"], name=tier), row=2, col=1)
    fig.update_layout(barmode="stack", template="plotly_white", legend_title_text="tier",
                      title=f"Locked slot consulté dans {df_events.loc[df_events['element'] == 'locked_slot', 'session_id'].nunique()} visites")
    return fig.to_json()
