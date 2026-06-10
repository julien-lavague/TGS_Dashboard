import asyncio
from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from db.supabase_client import get_dataframe
from core.user_segments import filter_users


DEV_ORIGIN = "https://dev.thegoodspots.fr/"


def _filter_dev_urls(df: pd.DataFrame) -> pd.DataFrame:
    if "page_url" not in df.columns:
        return df
    return df[~df["page_url"].str.startswith(DEV_ORIGIN, na=False)]


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

    buttons = [dict(
        label="All Users", method="update",
        args=[
            {"x": [t.x for t in fig.data], "y": [t.y for t in fig.data], "visible": [True] * len(fig.data)},
            {"title": "Page Views by Type Over Time (All Users)"},
        ],
    )]
    for email in all_emails:
        df_e = df_timeline[df_timeline["email"] == email]
        new_data = []
        for trace in fig.data:
            df_pt = df_e[df_e["page_type"] == trace.name]
            new_data.append({"x": df_pt["entry_date"].tolist(), "y": df_pt["count"].tolist()})
        buttons.append(dict(
            label=email, method="update",
            args=[
                {"x": [d["x"] for d in new_data], "y": [d["y"] for d in new_data], "visible": [True] * len(fig.data)},
                {"title": f"Page Views — {email}"},
            ],
        ))

    fig.update_layout(
        updatemenus=[dict(
            active=0, buttons=buttons,
            x=0.0, xanchor="left", y=1.2, yanchor="top", bgcolor="lightgray",
        )],
        xaxis=dict(tickformat="%Y-%m-%d", tickangle=-45),
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
        xaxis=dict(tickformat="%Y-%m-%d", tickangle=-45),
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
        xaxis=dict(tickformat="%Y-%m-%d", tickangle=-45),
        bargap=0.2,
        height=600,
        margin=dict(t=150),
    )
    return fig.to_json()


async def get_daily_active_users_figure(segment: str, days: Optional[int] = None) -> str:
    # Always load the full history — days only controls granularity, not the date range.
    # Filtering to a short window would make the cumulative appear flat because most
    # users first joined before the window starts.
    df_analytics, df_users = await asyncio.gather(
        get_dataframe("user_analytics"),
        get_dataframe("users"),
    )
    df_filtered_users = filter_users(df_users, segment)
    df_analytics = _filter_dev_urls(df_analytics)

    if days is None:
        freq, period_label, tick_fmt = "M", "Month", "%Y-%m"
    elif days <= 7:
        freq, period_label, tick_fmt = "D", "Day", "%Y-%m-%d"
    else:
        freq, period_label, tick_fmt = "W", "Week", "%Y-W%V"

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

    # --- Cumulative unique signed-in users ---
    df_signed = df_analytics[df_analytics["_uid_str"].isin(segment_user_ids)]
    df_seen = df_signed.drop_duplicates(subset=["_uid_str", "period"])[["_uid_str", "period"]]

    if not df_seen.empty and all_periods:
        df_pivot = (
            df_seen.assign(active=1)
            .pivot_table(index="period", columns="_uid_str", values="active", aggfunc="max")
            .reindex(index=all_periods)
            .fillna(0)
            .sort_index()
            .cummax()
        )
        cumul_signed = df_pivot.sum(axis=1).rename("signed_in_users")
    else:
        cumul_signed = pd.Series(0, index=pd.Index(all_periods), name="signed_in_users")

    # --- Anonymous visits per period (user_id is null) ---
    df_anon = df_analytics[df_analytics["user_id"].isna()]
    anon_by_period = df_anon.groupby("period").size().rename("anonymous_visits")

    df_combined = (
        pd.DataFrame({"period": all_periods})
        .set_index("period")
        .join(cumul_signed)
        .join(anon_by_period)
        .fillna(0)
        .reset_index()
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_combined["period"],
        y=df_combined["signed_in_users"],
        name="Signed-in Users (cumul.)",
        marker_color="#636EFA",
    ))
    fig.add_trace(go.Bar(
        x=df_combined["period"],
        y=df_combined["anonymous_visits"],
        name="Anonymous Visits",
        marker_color="#EF553B",
    ))

    fig.update_layout(
        title=f"Cumulative Signed-in Users & Anonymous Visits per {period_label}",
        barmode="group",
        xaxis=dict(tickformat=tick_fmt, tickangle=-45),
        yaxis=dict(tickformat="d", title="Count"),
        bargap=0.2,
        height=600,
        margin=dict(t=100),
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

    if days == 1:
        period_label = "Last Day"
    elif days == 7:
        period_label = "Last Week"
    elif days == 30:
        period_label = "Last Month"
    else:
        period_label = "All Time"

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
