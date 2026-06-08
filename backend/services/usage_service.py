import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from db.supabase_client import get_dataframe
from core.user_segments import filter_users


async def _load_analytics_merged(segment: str) -> pd.DataFrame:
    df_analytics, df_users = await asyncio.gather(
        get_dataframe("user_analytics"),
        get_dataframe("users"),
    )
    df_filtered_users = filter_users(df_users, segment)

    df_merged = df_analytics.merge(
        df_filtered_users[["id", "email"]],
        left_on="user_id", right_on="id", suffixes=("", "_user"),
    )
    return df_merged


async def get_page_views_figure(segment: str) -> str:
    df = await _load_analytics_merged(segment)

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


async def get_sessions_figure(segment: str) -> str:
    df = await _load_analytics_merged(segment)

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


async def get_sessions_per_week_since_signup_figure(segment: str) -> str:
    df_analytics, df_users = await asyncio.gather(
        get_dataframe("user_analytics"),
        get_dataframe("users"),
    )
    df_filtered_users = filter_users(df_users, segment)

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


async def get_timeline_figure(segment: str) -> str:
    df = await _load_analytics_merged(segment)

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
