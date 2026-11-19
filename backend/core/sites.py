"""Site d'origine des visites : la prod ou dev.thegoodspots.fr.

L'app écrit prod et dev dans les mêmes tables Supabase ; seul `page_url`
permet de les distinguer.
"""
import pandas as pd

SITES = ("prod", "dev")
DEV_ORIGIN = "https://dev.thegoodspots.fr/"
LOCAL_ORIGINS = ("http://localhost", "http://127.0.0.1")


def filter_site(df: pd.DataFrame, site: str = "prod") -> pd.DataFrame:
    """Ne garde que les lignes du site demandé (les postes locaux sont toujours exclus)."""
    if df.empty or "page_url" not in df.columns:
        return df
    urls = df["page_url"].fillna("")
    is_dev = urls.str.startswith(DEV_ORIGIN)
    if site == "dev":
        return df[is_dev]
    return df[~is_dev & ~urls.str.startswith(LOCAL_ORIGINS)]
