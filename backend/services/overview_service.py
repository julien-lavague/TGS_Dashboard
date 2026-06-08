import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from db.supabase_client import get_dataframe
from core.user_segments import filter_users


async def get_user_growth_figure(segment: str) -> str:
    df_users = await get_dataframe("users")
    df_filtered = filter_users(df_users, segment)

    df_filtered = df_filtered.copy()
    df_filtered["created_at"] = pd.to_datetime(df_filtered["created_at"], utc=True)
    df_sorted = df_filtered.sort_values("created_at")

    df_sorted["week"] = (
        df_sorted["created_at"]
        .dt.tz_localize(None)
        .dt.to_period("W")
        .apply(lambda r: r.start_time)
    )
    df_weekly = df_sorted.groupby("week").size().reset_index(name="new_users")

    fig = px.bar(
        df_weekly,
        x="week",
        y="new_users",
        title="New Users Per Week",
        labels={"week": "Week", "new_users": "New Users"},
    )
    fig.update_layout(xaxis_tickformat="%Y-%m-%d")
    return fig.to_json()


async def get_messages_over_time_figure(segment: str) -> str:
    df_users, df_conversations, df_messages = await asyncio.gather(
        get_dataframe("users"),
        get_dataframe("conversations"),
        get_dataframe("messages"),
    )

    df_filtered_users = filter_users(df_users, segment)

    merged = (
        df_messages
        .merge(
            df_conversations[["id", "user_id"]],
            left_on="conversation_id", right_on="id", suffixes=("", "_conv"),
        )
        .merge(
            df_users[["id", "email"]],
            left_on="user_id", right_on="id", suffixes=("", "_user"),
        )
    )

    merged = merged[merged["email"].isin(df_filtered_users["email"])]
    merged = merged[merged["role"] == "user"]

    merged["created_at_dt"] = pd.to_datetime(merged["created_at"])
    merged["date"] = merged["created_at_dt"].dt.date

    msg_per_day = (
        merged.groupby(["date", "email"]).size().reset_index(name="num_messages")
    )
    msg_per_day["date"] = pd.to_datetime(msg_per_day["date"])

    emails = sorted(msg_per_day["email"].unique())
    fig = go.Figure()

    all_agg = msg_per_day.groupby("date")["num_messages"].sum().reset_index()
    fig.add_trace(go.Bar(x=all_agg["date"], y=all_agg["num_messages"], name="All Users", visible=True))

    for email in emails:
        df_e = msg_per_day[msg_per_day["email"] == email]
        fig.add_trace(go.Bar(x=df_e["date"], y=df_e["num_messages"], name=email, visible=False))

    buttons = []
    buttons.append(dict(
        label="Stacked (All)", method="update",
        args=[{"visible": [False] + [True] * len(emails)}, {"title": "Messages Over Time — Stacked", "barmode": "stack"}],
    ))
    buttons.append(dict(
        label="All Users", method="update",
        args=[{"visible": [True] + [False] * len(emails)}, {"title": "Messages Over Time — All Users"}],
    ))
    for i, email in enumerate(emails):
        vis = [False] * (1 + len(emails))
        vis[i + 1] = True
        buttons.append(dict(
            label=email, method="update",
            args=[{"visible": vis}, {"title": f"Messages — {email}"}],
        ))

    fig.update_layout(
        updatemenus=[dict(
            active=1, buttons=buttons,
            direction="down", x=0.0, xanchor="left", y=1.15, yanchor="top",
        )],
        title="Messages Over Time — All Users",
        xaxis_title="Date",
        yaxis_title="Number of Messages",
        xaxis_tickformat="%Y-%m-%d",
        bargap=0.3,
    )
    return fig.to_json()
