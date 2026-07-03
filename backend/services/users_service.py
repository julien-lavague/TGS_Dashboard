import pandas as pd

from db.supabase_client import get_dataframe
from core.user_segments import (
    LST_TESTING,
    LST_BETA,
    LST_FRIENDS,
    LST_WORK,
    LST_ALL_NON_RELEASE,
)

DEV_ORIGIN = "https://dev.thegoodspots.fr/"


def _filter_dev_urls(df: pd.DataFrame) -> pd.DataFrame:
    if "page_url" not in df.columns:
        return df
    return df[~df["page_url"].str.startswith(DEV_ORIGIN, na=False)]


async def get_users_by_segment() -> dict[str, list[str]]:
    df = await get_dataframe("users")
    all_emails: set[str] = set(df["email"].dropna().tolist())

    release = sorted(all_emails - set(LST_ALL_NON_RELEASE))
    testing = sorted(all_emails & set(LST_TESTING))
    beta = sorted(all_emails & set(LST_BETA))
    friends = sorted(all_emails & set(LST_FRIENDS))
    work = sorted(all_emails & set(LST_WORK))

    return {
        "release": release,
        "testing": testing,
        "beta": beta,
        "friends": friends,
        "work": work,
    }


async def get_anonymous_visitor_stats() -> dict:
    df = await get_dataframe("user_analytics")
    df = _filter_dev_urls(df)
    anon = df[df["user_id"].isna()]
    session_count = int(anon["session_id"].nunique())
    page_view_count = int(len(anon))
    last_seen = (
        pd.to_datetime(anon["entry_time"], format="mixed").max().date().isoformat()
        if not anon.empty
        else None
    )
    return {"session_count": session_count, "page_view_count": page_view_count, "last_seen": last_seen}
