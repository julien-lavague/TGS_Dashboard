import asyncio
from anthropic import Anthropic

from db.supabase_client import get_dataframe
from core.user_segments import filter_users
from config import settings


async def analyze_topics(segment: str) -> dict[str, str]:
    df_users, df_conversations, df_messages = await asyncio.gather(
        get_dataframe("users"),
        get_dataframe("conversations"),
        get_dataframe("messages"),
    )

    df_filtered = filter_users(df_users, segment)

    merged = (
        df_messages
        .merge(df_conversations[["id", "user_id"]], left_on="conversation_id", right_on="id", suffixes=("", "_conv"))
        .merge(df_users[["id", "email"]], left_on="user_id", right_on="id", suffixes=("", "_user"))
    )
    merged = merged[merged["email"].isin(df_filtered["email"])]
    user_messages = merged[merged["role"] == "user"]

    client = Anthropic(api_key=settings.anthropic_api_key)
    loop = asyncio.get_event_loop()

    async def call_for_user(email: str) -> tuple[str, str]:
        msgs = user_messages[user_messages["email"] == email]
        if msgs.empty:
            return email, "Aucun message trouvé."

        questions_list = "\n".join(
            f"{i + 1}. {row['content']}"
            for i, (_, row) in enumerate(msgs.iterrows())
        )
        prompt = (
            f"Voici les questions posées par un utilisateur d'une application d'assistance kitesurf/windsurf :\n\n"
            f"{questions_list}\n\n"
            f"Analyse ces questions et identifie les 5 principaux thèmes abordés. "
            f"Pour chaque thème, donne un court intitulé et une phrase de description. "
            f"Si moins de 5 thèmes distincts, liste autant que possible. "
            f"Réponds en français."
        )

        def _sync_call() -> str:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        result = await loop.run_in_executor(None, _sync_call)
        return email, result

    tasks = [call_for_user(email) for email in df_filtered["email"].tolist()]
    pairs = await asyncio.gather(*tasks, return_exceptions=True)

    results: dict[str, str] = {}
    for item in pairs:
        if isinstance(item, Exception):
            continue
        email, text = item
        results[email] = text

    return results
