import asyncio
import pandas as pd
from supabase import create_client
from config import settings


# PostgREST caps each response at 1000 rows by default, so we page through
# the table in fixed-size chunks until a short page signals the end.
_PAGE_SIZE = 1000


def _fetch_all_rows(table_name: str) -> list:
    # Create a fresh client per call to avoid sharing an HTTP/2 connection
    # across concurrent asyncio.to_thread calls, which triggers WinError 10035
    # (WSAEWOULDBLOCK) when multiple threads race on the same socket.
    client = create_client(settings.supabase_url, settings.supabase_api_key)
    rows: list = []
    offset = 0
    while True:
        page = (
            client.table(table_name)
            .select("*")
            .order("id")  # stable order so ranged pages don't skip/duplicate rows
            .range(offset, offset + _PAGE_SIZE - 1)
            .execute()
        )
        rows.extend(page.data)
        if len(page.data) < _PAGE_SIZE:
            break
        offset += _PAGE_SIZE
    return rows


async def get_dataframe(table_name: str) -> pd.DataFrame:
    rows = await asyncio.to_thread(_fetch_all_rows, table_name)
    return pd.DataFrame(rows)
