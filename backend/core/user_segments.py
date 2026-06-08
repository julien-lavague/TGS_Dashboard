import json
import pathlib
import pandas as pd

_data = json.loads((pathlib.Path(__file__).parent / "user_segments.json").read_text())

LST_TESTING = _data["testing"]
LST_BETA    = _data["beta"]
LST_FRIENDS = _data["friends"]
LST_WORK    = _data["work"]

LST_ALL_NON_RELEASE = LST_TESTING + LST_BETA + LST_FRIENDS + LST_WORK


def filter_users(df_users: pd.DataFrame, segment: str) -> pd.DataFrame:
    """Return the users DataFrame filtered to the requested segment.

    segment values:
      "release" — real users only (excludes all internal/beta/friends/work)
      "beta"    — early beta testers
      "all"     — everyone (no filter applied)
    """
    if segment == "beta":
        return df_users[df_users["email"].isin(LST_BETA)]
    if segment == "testing":
        return df_users[df_users["email"].isin(LST_TESTING)]
    if segment == "friends":
        return df_users[df_users["email"].isin(LST_FRIENDS)]
    if segment == "work":
        return df_users[df_users["email"].isin(LST_WORK)]
    if segment == "release":
        return df_users[~df_users["email"].isin(LST_ALL_NON_RELEASE)]
    return df_users  # "all"
