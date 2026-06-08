import pandas as pd
from db.supabase_client import get_dataframe
from schemas.alerts import AlertRow
from core.user_segments import filter_users


async def get_alert_schedule(segment: str = "release") -> list[AlertRow]:
    df_alerts, df_users = await _load_data()
    df_users = filter_users(df_users, segment)

    df = (
        df_alerts
        .merge(df_users[["id", "email"]], left_on="user_id", right_on="id", suffixes=("", "_user"))
    )

    df = df[["email", "name", "question", "schedule", "is_active"]].copy()

    # Explode nested schedule list → one row per day
    df = df.explode("schedule").reset_index(drop=True)
    df["day"] = df["schedule"].apply(lambda x: x.get("day") if isinstance(x, dict) else None)
    df["times"] = df["schedule"].apply(lambda x: x.get("times") if isinstance(x, dict) else None)

    # Explode times list → one row per time slot
    df = df.explode("times").reset_index(drop=True)
    df.rename(columns={"times": "time"}, inplace=True)
    df.drop(columns=["schedule"], inplace=True)

    return [
        AlertRow(
            email=row["email"],
            name=row["name"],
            question=row["question"],
            is_active=bool(row["is_active"]),
            day=row["day"],
            time=row["time"],
        )
        for _, row in df.iterrows()
    ]


async def _load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    import asyncio
    df_alerts, df_users = await asyncio.gather(
        get_dataframe("user_alerts"),
        get_dataframe("users"),
    )
    return df_alerts, df_users
