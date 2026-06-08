from db.supabase_client import get_dataframe
from core.user_segments import (
    LST_TESTING,
    LST_BETA,
    LST_FRIENDS,
    LST_WORK,
    LST_ALL_NON_RELEASE,
)


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
