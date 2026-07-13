import asyncio
from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from db.supabase_client import get_dataframe
from core.user_segments import filter_users


DEV_ORIGIN = "https://dev.thegoodspots.fr/"

# X-axis config for daily bar charts: one tick per day, weekday name above the
# date, and vertical gridlines so each bar clearly maps to its day.
DAILY_XAXIS = dict(
    tickformat="%a<br>%Y-%m-%d",
    tickangle=0,
    dtick="D1",
    ticklabelmode="period",
    showgrid=True,
    gridcolor="rgba(0,0,0,0.12)",
    ticks="outside",
)


def _filter_dev_urls(df: pd.DataFrame) -> pd.DataFrame:
    if "page_url" not in df.columns:
        return df
    return df[~df["page_url"].str.startswith(DEV_ORIGIN, na=False)]


def _rolling_window_days(days: Optional[int]) -> int:
    """Rolling window adapts to the displayed range: ~a month of smoothing for
    long/All-time views, ~a week for shorter ranges."""
    return 30 if (days is None or days > 30) else 7


def _rolling_by_type(
    df_sub: pd.DataFrame, page_types: list, window_days: int
) -> dict:
    """Trailing rolling-average of daily counts per page_type.

    Days with no rows are treated as 0 (a genuine no-views day) so the average
    isn't inflated by only counting active days. Returns {page_type: (xs, ys)}
    aligned to a continuous daily date range.
    """
    if df_sub.empty:
        return {pt: ([], []) for pt in page_types}
    daily = (
        df_sub.groupby(["entry_date", "page_type"])["count"].sum().reset_index()
    )
    pivot = (
        daily.pivot(index="entry_date", columns="page_type", values="count")
        .sort_index()
    )
    full_idx = pd.date_range(pivot.index.min(), pivot.index.max(), freq="D")
    pivot = pivot.reindex(full_idx).fillna(0)
    rolled = pivot.rolling(window=window_days, min_periods=1).mean().round(2)
    xs = rolled.index.tolist()
    return {
        pt: (xs, rolled[pt].tolist()) if pt in rolled.columns else ([], [])
        for pt in page_types
    }


def _apply_days_filter(df: pd.DataFrame, days: Optional[int]) -> pd.DataFrame:
    if days is None:
        return df
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days)
    entry_times = pd.to_datetime(df["entry_time"], format="mixed", utc=True)
    return df[entry_times >= cutoff]


async def _load_analytics_merged(segment: str, days: Optional[int] = None) -> pd.DataFrame:
    df_analytics, df_users = await asyncio.gather(
        get_dataframe("user_analytics"),
        get_dataframe("users"),
    )
    df_filtered_users = filter_users(df_users, segment)
    df_analytics = _filter_dev_urls(df_analytics)
    df_analytics = _apply_days_filter(df_analytics, days)

    df_merged = df_analytics.merge(
        df_filtered_users[["id", "email"]],
        left_on="user_id", right_on="id", suffixes=("", "_user"),
    )
    return df_merged


async def get_page_views_figure(segment: str, days: Optional[int] = None) -> str:
    df = await _load_analytics_merged(segment, days)

    df["entry_date"] = pd.to_datetime(df["entry_time"], format="mixed").dt.date
    df_timeline = (
        df.groupby(["entry_date", "page_type", "email"])
        .size()
        .reset_index(name="count")
    )
    df_timeline["entry_date"] = pd.to_datetime(df_timeline["entry_date"])

    all_emails = sorted(df_timeline["email"].unique().tolist())

    fig = px.bar(
        df_timeline,
        x="entry_date", y="count", color="page_type",
        title="Page Views by Type Over Time (All Users)",
        labels={"entry_date": "Date", "count": "Page Views", "page_type": "Page Type"},
        barmode="stack",
    )

    # Page-type order + colors, captured before the rolling lines are appended.
    page_types = [t.name for t in fig.data]
    color_map = {t.name: t.marker.color for t in fig.data}

    window = _rolling_window_days(days)
    window_label = "30-day" if window == 30 else "7-day"

    # One trailing rolling-average line per page type, matching its bar colour.
    all_roll = _rolling_by_type(df_timeline, page_types, window)
    for pt in page_types:
        xs, ys = all_roll[pt]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, name=f"{pt} · {window_label} avg", mode="lines",
            line=dict(color=color_map.get(pt), width=2.5),
            legendgroup=pt,
            hovertemplate=f"{pt} {window_label} avg: %{{y}}<extra></extra>",
        ))

    n = len(page_types)

    def _button(label, df_sub, title):
        bar_x = [df_sub[df_sub["page_type"] == pt]["entry_date"].tolist() for pt in page_types]
        bar_y = [df_sub[df_sub["page_type"] == pt]["count"].tolist() for pt in page_types]
        roll = _rolling_by_type(df_sub, page_types, window)
        line_x = [roll[pt][0] for pt in page_types]
        line_y = [roll[pt][1] for pt in page_types]
        return dict(
            label=label, method="update",
            args=[
                {"x": bar_x + line_x, "y": bar_y + line_y, "visible": [True] * (2 * n)},
                {"title": title},
            ],
        )

    buttons = [_button("All Users", df_timeline, "Page Views by Type Over Time (All Users)")]
    for email in all_emails:
        df_e = df_timeline[df_timeline["email"] == email]
        buttons.append(_button(email, df_e, f"Page Views — {email}"))

    fig.update_layout(
        updatemenus=[dict(
            active=0, buttons=buttons,
            x=0.0, xanchor="left", y=1.2, yanchor="top", bgcolor="lightgray",
        )],
        xaxis=DAILY_XAXIS,
        bargap=0.2,
        height=600,
        margin=dict(t=150),
    )
    return fig.to_json()


async def get_sessions_figure(segment: str, days: Optional[int] = None) -> str:
    df = await _load_analytics_merged(segment, days)

    df["entry_date"] = pd.to_datetime(df["entry_time"], format="mixed").dt.date
    df_sessions = (
        df.dropna(subset=["email"])
        .drop_duplicates(subset=["session_id", "email", "entry_date"])
        .groupby(["entry_date", "email"])
        .agg(session_count=("session_id", "nunique"))
        .reset_index()
    )
    df_sessions["entry_date"] = pd.to_datetime(df_sessions["entry_date"])

    all_emails = df_sessions["email"].unique().tolist()

    fig = px.bar(
        df_sessions,
        x="entry_date", y="session_count", color="email",
        title="Sessions per User Over Time",
        labels={"entry_date": "Date", "session_count": "Sessions", "email": "User"},
        barmode="stack",
    )

    buttons = [dict(
        label="All Users", method="update",
        args=[{"visible": [True] * len(all_emails)}, {"title": "Sessions per User Over Time (All Users)"}],
    )]
    for email in all_emails:
        vis = [t.name == email for t in fig.data]
        buttons.append(dict(
            label=email, method="update",
            args=[{"visible": vis}, {"title": f"Sessions — {email}"}],
        ))

    fig.update_layout(
        updatemenus=[dict(
            active=0, buttons=buttons,
            x=0.0, xanchor="left", y=1.2, yanchor="top", bgcolor="lightgray",
        )],
        xaxis=DAILY_XAXIS,
        bargap=0.2,
        height=600,
        margin=dict(t=150),
    )
    return fig.to_json()


async def get_sessions_per_week_since_signup_figure(segment: str, days: Optional[int] = None) -> str:
    df_analytics, df_users = await asyncio.gather(
        get_dataframe("user_analytics"),
        get_dataframe("users"),
    )
    df_filtered_users = filter_users(df_users, segment)
    df_analytics = _filter_dev_urls(df_analytics)
    df_analytics = _apply_days_filter(df_analytics, days)

    df_merged = df_analytics.merge(
        df_filtered_users[["id", "email", "created_at"]],
        left_on="user_id", right_on="id", suffixes=("", "_user"),
    )

    df_merged["entry_time_dt"] = pd.to_datetime(df_merged["entry_time"], format="mixed", utc=True)
    df_merged["created_at_dt"] = pd.to_datetime(df_merged["created_at"], format="mixed", utc=True)
    df_merged["week_since_signup"] = (
        (df_merged["entry_time_dt"] - df_merged["created_at_dt"]).dt.days // 7
    )
    df_merged = df_merged[df_merged["week_since_signup"] >= 0]

    df_weekly = (
        df_merged.dropna(subset=["email", "session_id"])
        .drop_duplicates(subset=["session_id"])
        .groupby(["week_since_signup", "email"])
        .agg(session_count=("session_id", "nunique"))
        .reset_index()
    )

    all_emails = sorted(df_weekly["email"].unique().tolist())

    fig = px.bar(
        df_weekly,
        x="week_since_signup", y="session_count", color="email",
        title="Sessions per Week Since Signup (All Users)",
        labels={"week_since_signup": "Week Since Signup", "session_count": "Sessions", "email": "User"},
        barmode="stack",
    )

    buttons = [dict(
        label="All Users", method="update",
        args=[{"visible": [True] * len(all_emails)}, {"title": "Sessions per Week Since Signup (All Users)"}],
    )]
    for email in all_emails:
        vis = [t.name == email for t in fig.data]
        buttons.append(dict(
            label=email, method="update",
            args=[{"visible": vis}, {"title": f"Sessions per Week Since Signup — {email}"}],
        ))

    fig.update_layout(
        updatemenus=[dict(
            active=0, buttons=buttons,
            x=0.0, xanchor="left", y=1.2, yanchor="top", bgcolor="lightgray",
        )],
        xaxis=dict(dtick=1, title="Week Since Signup"),
        bargap=0.2,
        height=600,
        margin=dict(t=150),
    )
    return fig.to_json()


async def get_visit_duration_figure(segment: str, days: Optional[int] = None) -> str:
    df = await _load_analytics_merged(segment, days)

    df["entry_date"] = pd.to_datetime(df["entry_time"], format="mixed").dt.date
    df_dur = (
        df.dropna(subset=["duration_seconds"])
        .groupby(["entry_date", "page_type"])
        .agg(total_minutes=("duration_seconds", lambda x: x.sum() / 60))
        .reset_index()
    )
    df_dur["entry_date"] = pd.to_datetime(df_dur["entry_date"])
    df_dur["total_minutes"] = df_dur["total_minutes"].round(2)

    page_types = sorted(df_dur["page_type"].unique().tolist())

    fig = px.bar(
        df_dur,
        x="entry_date", y="total_minutes", color="page_type",
        title="Visit Duration by Page Type Over Time (All Pages)",
        labels={"entry_date": "Date", "total_minutes": "Duration (min)", "page_type": "Page Type"},
        barmode="stack",
        category_orders={"page_type": page_types},
    )

    buttons = [dict(
        label="All Pages", method="update",
        args=[{"visible": [True] * len(fig.data)}, {"title": "Visit Duration by Page Type Over Time (All Pages)"}],
    )]
    for pt in page_types:
        vis = [t.name == pt for t in fig.data]
        buttons.append(dict(
            label=pt, method="update",
            args=[{"visible": vis}, {"title": f"Visit Duration — {pt}"}],
        ))

    fig.update_layout(
        updatemenus=[dict(
            active=0, buttons=buttons,
            x=0.0, xanchor="left", y=1.2, yanchor="top", bgcolor="lightgray",
        )],
        xaxis=DAILY_XAXIS,
        bargap=0.2,
        height=600,
        margin=dict(t=150),
    )
    return fig.to_json()


async def get_daily_active_users_figure(segment: str, days: Optional[int] = None) -> str:
    df_analytics, df_users = await asyncio.gather(
        get_dataframe("user_analytics"),
        get_dataframe("users"),
    )
    df_filtered_users = filter_users(df_users, segment)
    df_analytics = _filter_dev_urls(df_analytics).copy()
    df_analytics = _apply_days_filter(df_analytics, days)

    # Granularity by displayed range: week filters (≤3 weeks) → daily bars,
    # month filter → weekly bars, All-time → monthly bars.
    if days is None:
        freq, period_label, tick_fmt, tick_dtick = "M", "Month", "%Y-%m", "M1"
    elif days <= 21:
        freq, period_label, tick_fmt, tick_dtick = "D", "Day", "%a<br>%Y-%m-%d", "D1"
    else:
        freq, period_label, tick_fmt, tick_dtick = "W", "Week", "%Y-W%V", 7 * 86400000

    df_analytics["entry_dt"] = pd.to_datetime(df_analytics["entry_time"], format="mixed", utc=True)
    df_analytics["period"] = df_analytics["entry_dt"].dt.to_period(freq).dt.to_timestamp()

    # Normalise to str so int vs uuid mismatches don't silently zero the join.
    segment_user_ids = set(df_filtered_users["id"].dropna().astype(str).tolist())
    df_analytics["_uid_str"] = df_analytics["user_id"].astype(str)

    # Build a contiguous period range (fills gaps where nobody visited).
    all_periods_raw = sorted(df_analytics["period"].unique())
    if all_periods_raw:
        full_range = pd.period_range(
            pd.Timestamp(all_periods_raw[0]).to_period(freq),
            pd.Timestamp(all_periods_raw[-1]).to_period(freq),
            freq=freq,
        )
        all_periods = [p.to_timestamp() for p in full_range]
    else:
        all_periods = []

    # --- Distinct signed-in users active in each period (not cumulative) ---
    id_to_email = dict(
        zip(df_filtered_users["id"].dropna().astype(str), df_filtered_users["email"])
    )
    df_signed = df_analytics[df_analytics["_uid_str"].isin(segment_user_ids)].copy()
    df_signed["email"] = df_signed["_uid_str"].map(id_to_email)
    df_seen = df_signed.drop_duplicates(subset=["_uid_str", "period"])
    signed_by_period = df_seen.groupby("period").size().rename("signed_in_users")

    # --- Anonymous visits per period (user_id is null) ---
    df_anon = df_analytics[df_analytics["user_id"].isna()]
    anon_by_period = df_anon.groupby("period").size().rename("anonymous_visits")

    df_combined = (
        pd.DataFrame({"period": all_periods})
        .set_index("period")
        .join(signed_by_period)
        .join(anon_by_period)
        .fillna(0)
        .reset_index()
    )

    # --- Per-user presence (1 if that user was active in the period, else 0) ---
    # Stacks to exactly the aggregate signed-in count, so the two views stay consistent.
    if not df_seen.empty:
        per_user = (
            df_seen.assign(active=1)
            .pivot_table(index="period", columns="email", values="active", aggfunc="max")
            .reindex(index=all_periods)
            .fillna(0)
        )
    else:
        per_user = pd.DataFrame(index=pd.Index(all_periods))
    user_emails = sorted(per_user.columns.tolist())

    # --- Per-visitor presence among anonymous rows carrying a visitor_id ---
    # visitor_id is a persistent per-browser id set client-side; it was only rolled
    # out ~2026-06, and clients blocking cookies/localStorage never get one. So only a
    # subset of anonymous rows can be attributed to a recurring visitor.
    has_vid = df_anon["visitor_id"].notna() & (
        df_anon["visitor_id"].astype(str).str.strip().ne("")
    )
    df_anon_id = df_anon[has_vid].copy()
    df_anon_noid = df_anon[~has_vid]
    # Untracked sessions can't be tied to a visitor — reported, not attributed.
    n_untracked_sessions = int(df_anon_noid["session_id"].nunique())

    if not df_anon_id.empty:
        # "Recurring" = seen on 2+ distinct calendar days (independent of chart granularity).
        days_per_vid = (
            df_anon_id.assign(_day=df_anon_id["entry_dt"].dt.date)
            .groupby("visitor_id")["_day"].nunique()
        )
        recurring_ids = sorted(days_per_vid[days_per_vid >= 2].index.tolist())
        onetime_ids = sorted(days_per_vid[days_per_vid < 2].index.tolist())
        per_visitor = (
            df_anon_id.drop_duplicates(subset=["visitor_id", "period"])
            .assign(active=1)
            .pivot_table(index="period", columns="visitor_id", values="active", aggfunc="max")
            .reindex(index=all_periods)
            .fillna(0)
        )
    else:
        recurring_ids, onetime_ids = [], []
        per_visitor = pd.DataFrame(index=pd.Index(all_periods))

    # Non-recurring tracked visitors collapsed into a single per-period count.
    if onetime_ids:
        onetime_by_period = per_visitor[onetime_ids].sum(axis=1)
    else:
        onetime_by_period = pd.Series(0.0, index=pd.Index(all_periods))

    fig = go.Figure()

    # Aggregate ("gross mass") traces — indices 0 and 1.
    fig.add_trace(go.Bar(
        x=df_combined["period"],
        y=df_combined["signed_in_users"],
        name="Signed-in Users",
        marker_color="#636EFA",
    ))
    fig.add_trace(go.Bar(
        x=df_combined["period"],
        y=df_combined["anonymous_visits"],
        name="Anonymous Visits",
        marker_color="#EF553B",
    ))

    # Detailed per-user traces — hidden by default.
    for email in user_emails:
        fig.add_trace(go.Bar(
            x=all_periods,
            y=per_user[email].tolist(),
            name=email,
            visible=False,
        ))

    # Detailed-visitor traces — hidden by default. Only anonymous rows with a
    # visitor_id can be attributed; the untracked bulk is counted in the title only,
    # so recurring visitors stay visible instead of being buried under it.
    fig.add_trace(go.Bar(
        x=all_periods,
        y=onetime_by_period.tolist(),
        name="One-time visitors",
        marker_color="#C9CBCF",
        visible=False,
        hovertemplate="One-time visitors: %{y}<extra></extra>",
    ))
    for vid in recurring_ids:
        fig.add_trace(go.Bar(
            x=all_periods,
            y=per_visitor[vid].tolist(),
            name=f"{str(vid)[:8]}…",
            visible=False,
            hovertemplate=f"Recurring visitor {str(vid)[:12]}…: %{{y}}<extra></extra>",
        ))

    # Rolling-average trend lines over the aggregate series — window is a few
    # periods wide, scaled to the display granularity (≈week for daily bars,
    # ≈month for weekly bars). Shown only in the Gross-mass view.
    window_periods = {"D": 7, "W": 4, "M": 3}[freq]
    trend_label = f"{window_periods}-{period_label.lower()} avg"
    signed_trend = (
        df_combined["signed_in_users"].rolling(window_periods, min_periods=1).mean().round(2)
    )
    anon_trend = (
        df_combined["anonymous_visits"].rolling(window_periods, min_periods=1).mean().round(2)
    )
    fig.add_trace(go.Scatter(
        x=df_combined["period"], y=signed_trend,
        name=f"Signed-in · {trend_label}", mode="lines",
        line=dict(color="#636EFA", width=2.5, dash="dot"),
        hovertemplate=f"Signed-in {trend_label}: %{{y}}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df_combined["period"], y=anon_trend,
        name=f"Anonymous · {trend_label}", mode="lines",
        line=dict(color="#EF553B", width=2.5, dash="dot"),
        hovertemplate=f"Anonymous {trend_label}: %{{y}}<extra></extra>",
    ))

    n_users = len(user_emails)
    n_vis = 1 + len(recurring_ids)  # one-time bucket + one bar per recurring visitor
    gross_title = f"Active Signed-in Users & Anonymous Visits per {period_label}"
    detail_title = f"Active Signed-in Users (per user) per {period_label}"
    visitor_title = (
        f"Anonymous Visitors per {period_label} — "
        f"{len(recurring_ids)} recurring, {len(onetime_ids)} one-time "
        f"(+{n_untracked_sessions} untracked sessions w/o visitor_id)"
    )

    f_u, t_u = [False] * n_users, [True] * n_users
    f_v, t_v = [False] * n_vis, [True] * n_vis

    # Trailing [signed-in trend, anonymous trend] — only shown with the gross bars.
    trend_on, trend_off = [True, True], [False, False]

    buttons = [
        dict(
            label="Gross mass", method="update",
            args=[
                {"visible": [True, True] + f_u + f_v + trend_on},
                {"title": gross_title, "barmode": "group"},
            ],
        ),
        dict(
            label="Detailed signed-in", method="update",
            args=[
                {"visible": [False, False] + t_u + f_v + trend_off},
                {"title": detail_title, "barmode": "stack"},
            ],
        ),
        dict(
            label="Detailed visitors", method="update",
            args=[
                {"visible": [False, False] + f_u + t_v + trend_off},
                {"title": visitor_title, "barmode": "stack"},
            ],
        ),
    ]

    fig.update_layout(
        title=gross_title,
        barmode="group",
        updatemenus=[dict(
            type="buttons", direction="right", active=0, buttons=buttons,
            x=0.0, xanchor="left", y=1.18, yanchor="top",
            pad=dict(r=6, t=4), bgcolor="lightgray",
        )],
        xaxis=dict(
            tickformat=tick_fmt,
            tickangle=0 if freq == "D" else -45,
            dtick=tick_dtick,
            ticklabelmode="period",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.12)",
            ticks="outside",
        ),
        yaxis=dict(tickformat="d", title="Count"),
        bargap=0.2,
        height=600,
        margin=dict(t=140),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig.to_json()


async def get_visit_frequency_figure(segment: str, days: Optional[int] = None) -> str:
    df_analytics, df_users = await asyncio.gather(
        get_dataframe("user_analytics"),
        get_dataframe("users"),
    )
    df_filtered_users = filter_users(df_users, segment)
    df_analytics = _filter_dev_urls(df_analytics)
    df_analytics = _apply_days_filter(df_analytics, days)

    df_merged = df_analytics.merge(
        df_filtered_users[["id", "email", "created_at"]],
        left_on="user_id", right_on="id",
        suffixes=("", "_user"),
    )

    now = pd.Timestamp.now(tz="UTC")
    df_merged["entry_time_dt"] = pd.to_datetime(df_merged["entry_time"], format="mixed", utc=True)
    df_merged["created_at_dt"] = pd.to_datetime(df_merged["created_at"], format="mixed", utc=True)

    # Count unique sessions per user within the filtered window
    df_user_stats = (
        df_merged.dropna(subset=["session_id"])
        .drop_duplicates(subset=["session_id"])
        .groupby(["email", "created_at_dt"])
        .agg(session_count=("session_id", "nunique"))
        .reset_index()
    )

    if days is not None:
        window_weeks = max(days / 7, 1 / 7)
        df_user_stats["visits_per_week"] = (df_user_stats["session_count"] / window_weeks).round(2)
        if days == 1:
            period_label = "last day (extrapolated/week)"
        elif days == 7:
            period_label = "last week"
        else:
            period_label = f"last {days} days (extrapolated/week)"
    else:
        df_user_stats["weeks_active"] = (
            (now - df_user_stats["created_at_dt"]).dt.total_seconds() / (7 * 24 * 3600)
        ).clip(lower=1 / 7)
        df_user_stats["visits_per_week"] = (
            df_user_stats["session_count"] / df_user_stats["weeks_active"]
        ).round(2)
        period_label = "since signup"

    df_sorted = df_user_stats.sort_values("visits_per_week", ascending=True)
    freq = df_user_stats["visits_per_week"]

    stats = {
        "Users": str(int(freq.count())),
        "Mean":  f"{freq.mean():.2f}",
        "Median": f"{freq.median():.2f}",
        "Min":   f"{freq.min():.2f}",
        "Max":   f"{freq.max():.2f}",
        "Std Dev": f"{freq.std():.2f}",
        "Variance": f"{freq.var():.2f}",
    }

    n_users = len(df_sorted)
    bar_height = max(300, n_users * 28)

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[bar_height, 120],
        vertical_spacing=0.06,
        specs=[[{"type": "xy"}], [{"type": "table"}]],
        subplot_titles=(
            f"Visit Frequency — {period_label}",
            "Statistics (visits / week across all users)",
        ),
    )

    fig.add_trace(
        go.Bar(
            y=df_sorted["email"],
            x=df_sorted["visits_per_week"],
            orientation="h",
            text=df_sorted["visits_per_week"],
            textposition="outside",
            marker_color="#636EFA",
            name="Visits / week",
        ),
        row=1, col=1,
    )

    fig.add_trace(
        go.Table(
            header=dict(
                values=list(stats.keys()),
                fill_color="#636EFA",
                font=dict(color="white", size=12),
                align="center",
                height=28,
            ),
            cells=dict(
                values=[[v] for v in stats.values()],
                fill_color="lavender",
                align="center",
                font=dict(size=12),
                height=28,
            ),
        ),
        row=2, col=1,
    )

    fig.update_xaxes(title_text="Visits per week", row=1, col=1)
    fig.update_layout(
        height=bar_height + 220,
        margin=dict(t=80, l=250, r=60, b=40),
        showlegend=False,
    )
    return fig.to_json()


async def get_user_visits_pareto_figure(segment: str, days: Optional[int] = None) -> str:
    df = await _load_analytics_merged(segment, days)

    df["entry_date"] = pd.to_datetime(df["entry_time"], format="mixed").dt.date

    df_visits = (
        df.drop_duplicates(subset=["user_id", "entry_date"])
        .groupby("email")
        .agg(day_visits=("entry_date", "count"))
        .reset_index()
        .sort_values("day_visits", ascending=False)
    )

    total = df_visits["day_visits"].sum()
    df_visits["cumulative_pct"] = df_visits["day_visits"].cumsum() / total * 100

    if days is None:
        period_label = "All Time"
    elif days == 1:
        period_label = "Last Day"
    elif days == 7:
        period_label = "Last Week"
    elif days == 30:
        period_label = "Last Month"
    elif days % 7 == 0:
        period_label = f"Last {days // 7} Weeks"
    else:
        period_label = f"Last {days} Days"

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_visits["email"],
        y=df_visits["day_visits"],
        name="Day Visits",
        marker_color="steelblue",
        yaxis="y",
    ))

    fig.add_trace(go.Scatter(
        x=df_visits["email"],
        y=df_visits["cumulative_pct"],
        name="Cumulative %",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="darkorange", width=2),
        marker=dict(size=6),
    ))

    fig.update_layout(
        title=f"User Day Visits — {period_label}",
        xaxis=dict(title="User", tickangle=-45),
        yaxis=dict(title="Day Visits"),
        yaxis2=dict(
            title="Cumulative %",
            overlaying="y",
            side="right",
            range=[0, 105],
            ticksuffix="%",
        ),
        bargap=0.2,
        height=600,
        margin=dict(t=100, b=180),
        legend=dict(x=0.5, y=1.08, xanchor="center", orientation="h"),
    )

    return fig.to_json()


async def get_timeline_figure(segment: str, days: Optional[int] = None) -> str:
    df = await _load_analytics_merged(segment, days)

    df_dur = (
        df.dropna(subset=["entry_time", "exit_time"])
        .assign(
            entry_time_dt=lambda x: pd.to_datetime(x["entry_time"], format="mixed"),
            exit_time_dt=lambda x: pd.to_datetime(x["exit_time"], format="mixed"),
        )
        .sort_values(["email", "entry_time"])
    )

    n_users = df_dur["email"].nunique()
    fig = px.timeline(
        df_dur,
        x_start="entry_time_dt", x_end="exit_time_dt",
        y="email", color="page_type",
        title="Time Spent on Each Page per User",
        labels={"email": "User", "page_type": "Page Type"},
        hover_data=["duration_seconds", "page_url"],
        category_orders={"page_type": sorted(df_dur["page_type"].unique().tolist())},
    )
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="User",
        height=400 + n_users * 60,
        margin=dict(t=100, l=250),
        xaxis=dict(tickformat="%Y-%m-%d %H:%M"),
    )
    fig.update_yaxes(autorange="reversed")
    return fig.to_json()
