import asyncio
import pandas as pd
from supabase import create_client, Client
from config import settings

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_api_key)
    return _client


async def get_dataframe(table_name: str) -> pd.DataFrame:
    client = get_client()
    data = await asyncio.to_thread(
        lambda: client.table(table_name).select("*").execute()
    )
    return pd.DataFrame(data.data)
